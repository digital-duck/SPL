"""Experiment 2: Token Budget Optimization Analysis.

Shows how SPL's optimizer allocates tokens under varying budgets
and handles over-budget scenarios with proportional compression.

Produces: Table 5 (Token Allocation), data for Figure 2 (stacked bars) and Figure 3 (compression).

Run: python -m tests.benchmarks.bench_token_optimization
"""

from __future__ import annotations

from tests.benchmarks.bench_utils import (
    parse_and_optimize, format_table, save_results,
)


# Template query with parameterized budget
QUERY_TEMPLATE = """\
PROMPT benchmark_query
WITH BUDGET {budget} tokens
USING MODEL claude-sonnet-4-5

SELECT
    system_role("You are a knowledgeable assistant"),
    context.question AS question LIMIT 200 tokens,
    rag.query("relevant docs", top_k=5) AS docs LIMIT {rag_limit} tokens,
    memory.get("history") AS history LIMIT {mem_limit} tokens

GENERATE
    answer(question, docs, history)
WITH OUTPUT BUDGET {output_budget} tokens, TEMPERATURE 0.3;
"""


def experiment_2a_varying_budgets():
    """2a: Same query structure, varying total budgets."""
    print("=" * 70)
    print("Experiment 2a: Token Allocation Under Varying Budgets")
    print("=" * 70)

    budgets = [2000, 4000, 8000, 16000, 32000]
    results = []

    for budget in budgets:
        # Scale output budget proportionally (25% of total)
        output_budget = budget // 4
        # RAG and memory limits scale but cap at reasonable values
        rag_limit = min(budget // 3, 8000)
        mem_limit = min(budget // 8, 2000)

        query = QUERY_TEMPLATE.format(
            budget=budget,
            rag_limit=rag_limit,
            mem_limit=mem_limit,
            output_budget=output_budget,
        )

        plans = parse_and_optimize(query)
        plan = plans[0]

        # Extract per-source allocations
        alloc = {}
        for step in plan.steps:
            alloc[step.alias] = step.allocated_tokens

        results.append({
            "budget": budget,
            "system": alloc.get("__system_role__", 0),
            "question": alloc.get("question", 0),
            "docs": alloc.get("docs", 0),
            "history": alloc.get("history", 0),
            "output": plan.output_budget,
            "buffer": plan.buffer_tokens,
            "input_total": plan.total_input_tokens,
            "utilization": round(
                (plan.total_input_tokens + plan.output_budget) / budget * 100, 1
            ) if budget else 0,
            "compressions": len([s for s in plan.steps if s.compressed]),
        })

    # Print table
    headers = ["Budget", "System", "Question", "RAG Docs", "Memory", "Output", "Buffer", "Util%"]
    rows = [
        [
            f"{r['budget']:,}",
            r["system"],
            r["question"],
            r["docs"],
            r["history"],
            r["output"],
            f"{r['buffer']:,}",
            f"{r['utilization']}%",
        ]
        for r in results
    ]
    print(format_table(headers, rows, "rrrrrrrr"))
    print()

    return results


def experiment_2b_over_budget():
    """2b: Fixed budget, increasing context sizes to trigger compression."""
    print("=" * 70)
    print("Experiment 2b: Compression Behavior Under Budget Pressure")
    print("=" * 70)

    budget = 4000
    output_budget = 1000
    # Vary context sizes: from comfortable to 4x over-budget
    context_multipliers = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    results = []

    for mult in context_multipliers:
        rag_limit = int(1500 * mult)
        mem_limit = int(500 * mult)

        query = QUERY_TEMPLATE.format(
            budget=budget,
            rag_limit=rag_limit,
            mem_limit=mem_limit,
            output_budget=output_budget,
        )

        plans = parse_and_optimize(query)
        plan = plans[0]

        total_requested = sum(s.limit_tokens or s.estimated_tokens for s in plan.steps)
        total_allocated = plan.total_input_tokens

        compressed_steps = [s for s in plan.steps if s.compressed]

        results.append({
            "multiplier": mult,
            "requested_tokens": total_requested,
            "allocated_tokens": total_allocated,
            "budget": budget,
            "output_budget": output_budget,
            "input_budget": budget - output_budget,
            "num_compressed": len(compressed_steps),
            "compression_ratios": {
                s.alias: round(s.compression_ratio, 3)
                for s in compressed_steps
            },
            "optimizations": plan.optimizations,
        })

    headers = ["Context Mult", "Requested", "Allocated", "Input Budget", "Compressed", "Optimizations"]
    rows = [
        [
            f"{r['multiplier']}x",
            f"{r['requested_tokens']:,}",
            f"{r['allocated_tokens']:,}",
            f"{r['input_budget']:,}",
            r["num_compressed"],
            len(r["optimizations"]),
        ]
        for r in results
    ]
    print(format_table(headers, rows, "rrrrrr"))
    print()

    # Show compression details for over-budget cases
    for r in results:
        if r["num_compressed"] > 0:
            print(f"  {r['multiplier']}x: ", end="")
            for alias, ratio in r["compression_ratios"].items():
                print(f"{alias}={ratio:.1%}", end=" ")
            print()

    return results


def experiment_2c_priority_ordering():
    """2c: Verify execution order follows priority (memory > RAG > context)."""
    print()
    print("=" * 70)
    print("Experiment 2c: Execution Priority Ordering")
    print("=" * 70)

    query = """\
PROMPT priority_test
WITH BUDGET 10000 tokens
SELECT
    system_role("test"),
    context.data AS data LIMIT 2000 tokens,
    memory.get("cache") AS cached LIMIT 500 tokens,
    rag.query("search", top_k=3) AS docs LIMIT 3000 tokens,
    context.extra AS extra LIMIT 1000 tokens,
    memory.get("profile") AS profile LIMIT 500 tokens
GENERATE response(data, cached, docs, extra, profile)
WITH OUTPUT BUDGET 3000 tokens;
"""

    plans = parse_and_optimize(query)
    plan = plans[0]

    print(f"\n  Execution order (priority → name → operation):")
    for i, step in enumerate(plan.steps):
        print(f"  {i + 1}. [{step.priority}] {step.alias:<20s} ({step.operation})")

    # Verify ordering
    priorities = [s.priority for s in plan.steps]
    is_sorted = priorities == sorted(priorities)
    print(f"\n  Priority ordering correct: {'YES' if is_sorted else 'NO'}")

    return {
        "steps": [
            {"order": i + 1, "priority": s.priority, "alias": s.alias, "operation": s.operation}
            for i, s in enumerate(plan.steps)
        ],
        "correctly_ordered": is_sorted,
    }


def run():
    results_2a = experiment_2a_varying_budgets()
    results_2b = experiment_2b_over_budget()
    results_2c = experiment_2c_priority_ordering()

    all_results = {
        "varying_budgets": results_2a,
        "over_budget": results_2b,
        "priority_ordering": results_2c,
    }

    path = save_results("experiment2_token_optimization", all_results)
    print(f"\nResults saved to: {path}")

    return all_results


if __name__ == "__main__":
    run()
