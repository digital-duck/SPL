"""Tests for SPL Optimizer and EXPLAIN."""

from spl.lexer import Lexer
from spl.parser import Parser
from spl.analyzer import Analyzer
from spl.optimizer import Optimizer, ExecutionPlan
from spl.explain import explain_plan


def optimize(source: str) -> list[ExecutionPlan]:
    """Helper: lex -> parse -> analyze -> optimize."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    return Optimizer().optimize(analysis)


class TestOptimizer:
    """Test the token budget optimizer."""

    def test_basic_plan(self):
        plans = optimize("""
            PROMPT test
            WITH BUDGET 5000 tokens
            SELECT
                system_role("test"),
                context.user AS user LIMIT 1000 tokens
            GENERATE response(user)
            WITH OUTPUT BUDGET 2000 tokens
        """)
        assert len(plans) == 1
        plan = plans[0]
        assert plan.prompt_name == "test"
        assert plan.total_budget == 5000
        assert plan.output_budget == 2000

    def test_token_allocation(self):
        plans = optimize("""
            PROMPT test
            WITH BUDGET 5000 tokens
            SELECT
                system_role("You are helpful"),
                context.data AS data LIMIT 1000 tokens,
                memory.get("history") AS history LIMIT 500 tokens
            GENERATE response(data, history)
            WITH OUTPUT BUDGET 2000 tokens
        """)
        plan = plans[0]
        # Each step should have allocated tokens
        for step in plan.steps:
            assert step.allocated_tokens > 0

    def test_execution_order(self):
        """Memory and cache should be fetched before context and RAG."""
        plans = optimize("""
            PROMPT test
            WITH BUDGET 10000 tokens
            SELECT
                context.data AS data LIMIT 2000 tokens,
                memory.get("cache") AS cached LIMIT 500 tokens,
                rag.query("search", top_k=3) AS docs LIMIT 3000 tokens
            GENERATE response(data, cached, docs)
            WITH OUTPUT BUDGET 3000 tokens
        """)
        plan = plans[0]
        # Steps should be sorted by priority
        priorities = [s.priority for s in plan.steps]
        assert priorities == sorted(priorities)

    def test_explain_output(self):
        plans = optimize("""
            PROMPT hello
            WITH BUDGET 5000 tokens
            USING MODEL claude-sonnet-4-5
            SELECT
                system_role("test"),
                context.user AS user LIMIT 1000 tokens
            GENERATE response(user)
            WITH OUTPUT BUDGET 2000 tokens
        """)
        output = explain_plan(plans[0])
        assert "hello" in output
        assert "tokens" in output
        assert "Token Allocation" in output
        assert "claude" in output

    def test_no_budget_works(self):
        """Queries without explicit budget should still produce a plan."""
        plans = optimize("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
        """)
        assert len(plans) == 1
        plan = plans[0]
        assert plan.total_budget is None

    def test_over_budget_compression(self):
        """When limits exceed budget, optimizer should compress."""
        plans = optimize("""
            PROMPT test
            WITH BUDGET 2000 tokens
            SELECT
                system_role("test"),
                context.data AS data LIMIT 3000 tokens,
                context.more AS more LIMIT 3000 tokens
            GENERATE response(data, more)
            WITH OUTPUT BUDGET 1000 tokens
        """)
        plan = plans[0]
        # Should have optimization messages
        assert len(plan.optimizations) > 0
