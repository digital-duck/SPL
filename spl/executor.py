"""SPL Executor: execute optimized plans against LLM backends."""

from __future__ import annotations
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field

_log = logging.getLogger("spl.executor")

from spl.ast_nodes import (
    PromptStatement, SelectItem, SystemRoleCall, ContextRef,
    RagQuery, MemoryGet, Identifier, Literal,
)
from spl.optimizer import ExecutionPlan, ExecutionStep
from spl.adapters import get_adapter
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.storage.memory import MemoryStore
from spl.storage.vector import VectorStore
from spl.storage import get_vector_store
from spl.token_counter import TokenCounter
from spl.functions import FunctionRegistry


@dataclass
class SPLResult:
    """Result of executing an SPL query."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float | None = None
    plan: ExecutionPlan | None = None
    context_used: dict[str, str] = field(default_factory=dict)


class Executor:
    """Execute SPL execution plans against LLM backends.

    Orchestrates: context gathering -> optimization -> LLM call -> result storage.
    """

    def __init__(
        self,
        adapter_name: str = "claude_cli",
        adapter: LLMAdapter | None = None,
        storage_dir: str = ".spl",
        vector_backend: str = "faiss",
        cache_enabled: bool = False,
        adapter_kwargs: dict | None = None,
    ):
        self.adapter = adapter or get_adapter(adapter_name, **(adapter_kwargs or {}))
        self.memory = MemoryStore(f"{storage_dir}/memory.db")
        self.functions = FunctionRegistry()
        self.cache_enabled = cache_enabled

        # Vector store is optional (only needed if RAG queries exist)
        self._vector_store: VectorStore | None = None
        self._storage_dir = storage_dir
        self._vector_backend = vector_backend

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = get_vector_store(self._vector_backend, self._storage_dir)
        return self._vector_store

    async def execute(
        self,
        plan: ExecutionPlan,
        params: dict[str, str] | None = None,
        stmt: PromptStatement | None = None,
    ) -> SPLResult:
        """Execute an optimized plan."""
        start = time.perf_counter()
        params = params or {}
        context_parts: dict[str, str] = {}
        system_prompt = None

        # Step 1a: Execute CTE sub-prompts in parallel (before regular context gathering)
        cte_steps = [s for s in plan.steps if s.operation == "cte" and s.cte_stmt is not None]
        if cte_steps:
            _log.info("[%s] dispatching %d CTE(s) in parallel: %s",
                      plan.prompt_name, len(cte_steps),
                      ", ".join(s.alias for s in cte_steps))
            cte_tasks = [self._execute_cte_step(s, params) for s in cte_steps]
            cte_results = await asyncio.gather(*cte_tasks)
            for step, result_text in zip(cte_steps, cte_results):
                context_parts[step.alias] = result_text
                _log.info("[%s] CTE '%s' completed (%d chars)",
                          plan.prompt_name, step.alias, len(result_text))

        # Step 1b: Gather context for each non-CTE step
        for step in plan.steps:
            if step.operation == "system_role":
                # Extract system prompt from the original statement
                system_prompt = self._resolve_system_role(step, stmt)
            elif step.operation == "load_context":
                context_parts[step.alias] = self._resolve_context(step, params)
            elif step.operation == "rag_query":
                context_parts[step.alias] = self._resolve_rag(step, stmt)
            elif step.operation == "memory_get":
                context_parts[step.alias] = self._resolve_memory(step)
            elif step.operation == "cte" and step.alias not in context_parts:
                context_parts[step.alias] = self._resolve_cte(step, context_parts)

        # Step 2: Apply token limits (truncation)
        counter = TokenCounter(plan.model)
        for step in plan.steps:
            if step.alias in context_parts and step.allocated_tokens > 0:
                text = context_parts[step.alias]
                if counter.count(text) > step.allocated_tokens:
                    context_parts[step.alias] = counter.truncate_to_tokens(
                        text, step.allocated_tokens
                    )

        # Step 3: Assemble the full prompt
        prompt = self._assemble_prompt(context_parts, plan, stmt)
        _log.info("[%s] assembled prompt  model=%s  budget=%d tokens",
                  plan.prompt_name, plan.model or "default", plan.output_budget)
        _log.debug("[%s] prompt text:\n%s", plan.prompt_name, prompt)

        # Step 4: Check cache (only when cache_enabled=True)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if self.cache_enabled:
            cached = self.memory.cache_get(prompt_hash)
            if cached:
                latency = (time.perf_counter() - start) * 1000
                return SPLResult(
                    content=cached,
                    model=plan.model or "cached",
                    input_tokens=0,
                    output_tokens=counter.count(cached),
                    total_tokens=counter.count(cached),
                    latency_ms=latency,
                    cost_usd=0.0,
                    plan=plan,
                    context_used=context_parts,
                )

        # Step 5: Call LLM
        _log.info("[%s] calling LLM ...", plan.prompt_name)
        gen_result = await self.adapter.generate(
            prompt=prompt,
            model=plan.model or "",
            max_tokens=plan.output_budget,
            temperature=self._get_temperature(stmt),
            system=system_prompt,
        )

        latency = (time.perf_counter() - start) * 1000
        _log.info("[%s] LLM response  model=%s  tokens=%d+%d=%d  latency=%.0fms",
                  plan.prompt_name, gen_result.model,
                  gen_result.input_tokens, gen_result.output_tokens,
                  gen_result.total_tokens, latency)
        _log.debug("[%s] response text:\n%s", plan.prompt_name, gen_result.content)

        # Step 6: Store result if STORE clause exists
        if stmt and stmt.store_clause:
            self.memory.set(stmt.store_clause.key, gen_result.content)

        # Step 7: Cache result (only when cache_enabled=True)
        if self.cache_enabled:
            self.memory.cache_set(prompt_hash, gen_result.content, plan.model or "")

        return SPLResult(
            content=gen_result.content,
            model=gen_result.model,
            input_tokens=gen_result.input_tokens,
            output_tokens=gen_result.output_tokens,
            total_tokens=gen_result.total_tokens,
            latency_ms=latency,
            cost_usd=gen_result.cost_usd,
            plan=plan,
            context_used=context_parts,
        )

    def _resolve_system_role(self, step: ExecutionStep, stmt: PromptStatement | None) -> str:
        """Extract system role text."""
        if stmt:
            for item in stmt.select_items:
                if isinstance(item.expression, SystemRoleCall):
                    return item.expression.description
        return "You are a helpful assistant."

    def _resolve_context(self, step: ExecutionStep, params: dict[str, str]) -> str:
        """Resolve context data from params."""
        # Look for the context field in params
        source = step.source  # e.g., "context.user_profile"
        if source.startswith("context."):
            field_name = source.split(".", 1)[1]
            # Check params with various key patterns
            for key in [source, field_name, f"context.{field_name}"]:
                if key in params:
                    return str(params[key])

        # Return placeholder if not provided
        return f"[Context: {step.alias} - not provided in params]"

    def _resolve_rag(self, step: ExecutionStep, stmt: PromptStatement | None) -> str:
        """Execute RAG query via FAISS vector store."""
        # Extract query text from the original statement
        query_text = step.source  # Simplified; would parse from RagQuery node
        if stmt:
            for item in stmt.select_items:
                if isinstance(item.expression, RagQuery):
                    query_expr = item.expression.query_text
                    if hasattr(query_expr, 'value'):
                        query_text = str(query_expr.value)

        try:
            results = self.vector_store.query(query_text, top_k=5)
            if results:
                return "\n\n".join(
                    f"[Document {r['id']}]: {r['text']}" for r in results
                )
            return "[No RAG results found]"
        except Exception:
            return "[RAG not initialized - run 'spl rag add' first]"

    def _resolve_memory(self, step: ExecutionStep) -> str:
        """Retrieve value from SQLite memory store."""
        # Extract key from source (e.g., 'memory.get("key")')
        key = step.alias  # Simplified; alias typically matches key
        value = self.memory.get(key)
        return value or f"[Memory key '{key}' not found]"

    def _resolve_cte(self, step: ExecutionStep, context: dict[str, str]) -> str:
        """Resolve CTE - already computed context."""
        return context.get(step.alias, f"[CTE '{step.alias}' not resolved]")

    async def _execute_cte_step(self, step: ExecutionStep, params: dict[str, str]) -> str:
        """Execute a CTE's nested PROMPT as a sub-query and return the result text."""
        from spl.optimizer import Optimizer
        cte_stmt = step.cte_stmt
        if cte_stmt is None:
            return f"[CTE '{step.alias}' has no nested PROMPT]"
        assert isinstance(cte_stmt, PromptStatement)
        _log.info("[CTE:%s] starting  model=%s", step.alias, cte_stmt.model or "default")
        sub_plan = Optimizer().optimize_single(cte_stmt)
        result = await self.execute(sub_plan, params=params, stmt=cte_stmt)
        _log.info("[CTE:%s] done  tokens=%d  latency=%.0fms",
                  step.alias, result.total_tokens, result.latency_ms)
        return result.content

    def _assemble_prompt(
        self,
        context: dict[str, str],
        plan: ExecutionPlan,
        stmt: PromptStatement | None,
    ) -> str:
        """Assemble the final prompt string from context parts."""
        parts = []

        for alias, text in context.items():
            if text and not text.startswith("["):
                parts.append(f"## {alias}\n{text}")

        # Add generate instruction
        if stmt and stmt.generate_clause:
            gen = stmt.generate_clause

            # Check for a user-defined function body
            func_def = self.functions.get(gen.function_name)
            if func_def:
                # Build param -> value mapping from GENERATE arguments
                arg_values: dict[str, str] = {}
                for param, arg in zip(func_def.parameters, gen.arguments):
                    if isinstance(arg, Identifier):
                        arg_values[param.name] = context.get(arg.name, "")
                    elif isinstance(arg, Literal):
                        arg_values[param.name] = str(arg.value)
                    else:
                        arg_values[param.name] = str(arg)
                # Substitute {param} placeholders in function body
                task_text = func_def.body
                for key, val in arg_values.items():
                    task_text = task_text.replace("{" + key + "}", val)
                parts.append(f"\n## Task\n{task_text}")

            else:
                # Look for a string literal argument as the instruction
                instruction = None
                for arg in gen.arguments:
                    if isinstance(arg, Literal) and arg.literal_type == "string":
                        instruction = str(arg.value)
                        break

                if instruction:
                    # Substitute {alias} placeholders with context values
                    for alias_key, val in context.items():
                        instruction = instruction.replace("{" + alias_key + "}", val)
                    parts.append(f"\n## Task\n{instruction}")
                else:
                    # Fallback: generic function call description
                    args_str = ", ".join(
                        a.name if isinstance(a, Identifier) else str(a)
                        for a in gen.arguments
                    )
                    parts.append(
                        f"\n## Task\n"
                        f"Based on the above context, generate: {gen.function_name}({args_str})"
                    )

            if gen.output_format:
                parts.append(f"Output format: {gen.output_format}")

        return "\n\n".join(parts)

    def _get_temperature(self, stmt: PromptStatement | None) -> float:
        if stmt and stmt.generate_clause and stmt.generate_clause.temperature is not None:
            return stmt.generate_clause.temperature
        return 0.7

    def close(self):
        """Clean up resources."""
        self.memory.close()
        if self._vector_store:
            self._vector_store.close()
