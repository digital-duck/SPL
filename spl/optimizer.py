"""SPL Optimizer: token budget allocation and execution planning."""

from __future__ import annotations
from dataclasses import dataclass, field
from spl.ast_nodes import (
    PromptStatement, SelectItem, SystemRoleCall, ContextRef,
    RagQuery, MemoryGet, Identifier, DottedName, FunctionCall,
)
from spl.analyzer import AnalysisResult
from spl.token_counter import TokenCounter


@dataclass
class ExecutionStep:
    """A single step in the execution plan."""
    operation: str      # "system_role", "load_context", "rag_query", "memory_get", "cte", "generate"
    source: str         # Human-readable source description
    alias: str          # Alias name
    estimated_tokens: int = 0
    limit_tokens: int | None = None
    allocated_tokens: int = 0
    compressed: bool = False
    compression_ratio: float = 1.0
    cache_status: str = "n/a"  # "hit", "miss", "n/a"
    priority: int = 0   # Lower = execute first
    cte_stmt: object = None  # PromptStatement for CTE nested PROMPT execution


@dataclass
class ExecutionPlan:
    """Complete optimized execution plan."""
    prompt_name: str
    model: str | None
    total_budget: int | None
    steps: list[ExecutionStep] = field(default_factory=list)
    output_budget: int = 0
    total_input_tokens: int = 0
    buffer_tokens: int = 0
    estimated_cost: float | None = None
    optimizations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Optimizer:
    """Optimize SPL queries for token efficiency."""

    def optimize(self, analysis: AnalysisResult) -> list[ExecutionPlan]:
        """Generate execution plans for all prompt statements."""
        plans = []
        for stmt in analysis.ast.statements:
            if isinstance(stmt, PromptStatement):
                plan = self._optimize_prompt(stmt)
                plans.append(plan)
        return plans

    def optimize_single(self, stmt: PromptStatement) -> ExecutionPlan:
        """Optimize a single prompt statement."""
        return self._optimize_prompt(stmt)

    def _optimize_prompt(self, stmt: PromptStatement) -> ExecutionPlan:
        counter = TokenCounter(stmt.model)
        plan = ExecutionPlan(
            prompt_name=stmt.name,
            model=stmt.model,
            total_budget=stmt.budget,
        )

        # Step 1: Create execution steps from SELECT items
        for item in stmt.select_items:
            step = self._create_step(item)
            plan.steps.append(step)

        # Step 2: Add CTE steps
        for cte in stmt.ctes:
            step = ExecutionStep(
                operation="cte",
                source=f"CTE: {cte.name}",
                alias=cte.name,
                estimated_tokens=cte.limit_tokens or 500,
                limit_tokens=cte.limit_tokens,
                allocated_tokens=cte.limit_tokens or 500,
                priority=1,
                cte_stmt=cte.nested_prompt,
            )
            plan.steps.append(step)

        # Step 3: Set output budget
        if stmt.generate_clause and stmt.generate_clause.output_budget:
            plan.output_budget = stmt.generate_clause.output_budget
        elif stmt.budget:
            # Default: allocate 40% to output if not specified
            plan.output_budget = int(stmt.budget * 0.4)
        else:
            plan.output_budget = 4096

        # Step 4: Optimize token allocation
        if stmt.budget:
            self._allocate_tokens(plan, stmt.budget, counter)
        else:
            # No budget constraint - just use limits or estimates as-is
            for step in plan.steps:
                step.allocated_tokens = step.limit_tokens or step.estimated_tokens

        # Step 5: Sort by priority (cached/memory first)
        plan.steps.sort(key=lambda s: s.priority)

        # Step 6: Calculate totals
        plan.total_input_tokens = sum(s.allocated_tokens for s in plan.steps)
        plan.buffer_tokens = max(0,
            (stmt.budget or 0) - plan.total_input_tokens - plan.output_budget
        )

        # Step 7: Estimate cost
        plan.estimated_cost = counter.estimate_cost(
            plan.total_input_tokens, plan.output_budget
        )

        return plan

    def _create_step(self, item: SelectItem) -> ExecutionStep:
        """Create an execution step from a SELECT item."""
        expr = item.expression
        alias = item.alias or self._infer_alias(expr)

        if isinstance(expr, SystemRoleCall):
            estimated = max(20, len(expr.description) // 4)
            return ExecutionStep(
                operation="system_role",
                source=f'system_role("{expr.description[:40]}...")',
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=0,
            )
        elif isinstance(expr, ContextRef):
            estimated = item.limit_tokens or 1000  # default estimate for context
            return ExecutionStep(
                operation="load_context",
                source=f"context.{expr.field_name}",
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=3,
            )
        elif isinstance(expr, RagQuery):
            top_k = expr.top_k or 5
            estimated = item.limit_tokens or top_k * 500  # ~500 tokens per doc
            return ExecutionStep(
                operation="rag_query",
                source=f"rag.query(top_k={top_k})",
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                cache_status="miss",
                priority=2,
            )
        elif isinstance(expr, MemoryGet):
            estimated = item.limit_tokens or 200
            return ExecutionStep(
                operation="memory_get",
                source=f'memory.get("{expr.key}")',
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=1,
            )
        else:
            estimated = item.limit_tokens or 500
            return ExecutionStep(
                operation="load_context",
                source=str(type(expr).__name__),
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=3,
            )

    def _allocate_tokens(self, plan: ExecutionPlan, budget: int, counter: TokenCounter):
        """Allocate tokens across steps to fit within budget."""
        available = budget - plan.output_budget

        # First pass: apply explicit limits
        total_allocated = 0
        unlimited_steps: list[ExecutionStep] = []

        for step in plan.steps:
            if step.limit_tokens is not None:
                step.allocated_tokens = min(step.limit_tokens, step.estimated_tokens)
                total_allocated += step.allocated_tokens
            else:
                unlimited_steps.append(step)

        # Second pass: distribute remaining budget to unlimited steps
        remaining = available - total_allocated
        if unlimited_steps and remaining > 0:
            per_step = remaining // len(unlimited_steps)
            for step in unlimited_steps:
                step.allocated_tokens = min(per_step, step.estimated_tokens)
                total_allocated += step.allocated_tokens

        # Third pass: compress if still over budget
        if total_allocated > available:
            plan.optimizations.append("Budget exceeded, applying proportional compression")
            overflow = total_allocated - available
            # Sort by allocated (compress largest first)
            sorted_steps = sorted(plan.steps, key=lambda s: s.allocated_tokens, reverse=True)
            for step in sorted_steps:
                if overflow <= 0:
                    break
                if step.operation == "system_role":
                    continue  # Don't compress system role
                reduction = min(step.allocated_tokens // 2, overflow)
                step.allocated_tokens -= reduction
                step.compressed = True
                step.compression_ratio = step.allocated_tokens / max(step.estimated_tokens, 1)
                overflow -= reduction
                plan.optimizations.append(
                    f"Compressed {step.alias}: {step.estimated_tokens} -> {step.allocated_tokens} tokens "
                    f"({step.compression_ratio:.0%})"
                )

    def _infer_alias(self, expr) -> str:
        """Infer an alias name from an expression."""
        if isinstance(expr, SystemRoleCall):
            return "__system_role__"
        elif isinstance(expr, ContextRef):
            return expr.field_name
        elif isinstance(expr, RagQuery):
            return "rag_results"
        elif isinstance(expr, MemoryGet):
            return expr.key
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, DottedName):
            return expr.parts[-1]
        elif isinstance(expr, FunctionCall):
            return expr.name
        return "unnamed"
