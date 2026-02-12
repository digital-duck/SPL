"""Experiment 3: Cost Estimation Across Models.

Demonstrates SPL's pre-execution cost visibility by running EXPLAIN
on the same query with different USING MODEL values.

Produces: Table 6 (Cross-Model Cost Estimation).

Run: python -m tests.benchmarks.bench_cost_estimation
"""

from __future__ import annotations

from tests.benchmarks.bench_utils import (
    parse_and_optimize, format_table, save_results,
)
from spl.token_counter import TokenCounter


QUERY_TEMPLATE = """\
PROMPT cost_benchmark
WITH BUDGET 8000 tokens
USING MODEL {model}

SELECT
    system_role("You are a knowledgeable assistant"),
    context.question AS question LIMIT 200 tokens,
    rag.query("relevant docs", top_k=5) AS docs LIMIT 3000 tokens,
    memory.get("history") AS history LIMIT 500 tokens

GENERATE
    answer(question, docs, history)
WITH OUTPUT BUDGET 2000 tokens, TEMPERATURE 0.3;
"""

MODELS = [
    ("claude-opus-4-6", "Claude Opus 4.6", "Premium"),
    ("claude-sonnet-4-5", "Claude Sonnet 4.5", "Balanced"),
    ("claude-haiku-4-5", "Claude Haiku 4.5", "Economy"),
    ("gpt-4o", "GPT-4o", "Flagship"),
    ("gpt-4", "GPT-4", "Legacy Premium"),
    ("gpt-3.5-turbo", "GPT-3.5 Turbo", "Budget"),
]


def run():
    print("=" * 70)
    print("Table 6: Cost Estimation Across Models (same 8K query)")
    print("=" * 70)

    results = []

    for model_id, model_name, tier in MODELS:
        query = QUERY_TEMPLATE.format(model=model_id)
        plans = parse_and_optimize(query)
        plan = plans[0]

        # Get pricing info
        counter = TokenCounter(model_id)
        input_tokens = plan.total_input_tokens
        output_tokens = plan.output_budget
        cost = counter.estimate_cost(input_tokens, output_tokens)

        results.append({
            "model_id": model_id,
            "model_name": model_name,
            "tier": tier,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": cost,
        })

    # Find cheapest for relative cost
    costs = [r["estimated_cost"] for r in results if r["estimated_cost"] is not None]
    min_cost = min(costs) if costs else 1

    for r in results:
        if r["estimated_cost"] is not None:
            r["relative_cost"] = round(r["estimated_cost"] / min_cost, 1)
        else:
            r["relative_cost"] = "N/A"

    headers = ["Model", "Tier", "Input Tokens", "Output Tokens", "Est. Cost", "Relative"]
    rows = [
        [
            r["model_name"],
            r["tier"],
            f"{r['input_tokens']:,}",
            f"{r['output_tokens']:,}",
            f"${r['estimated_cost']:.4f}" if r["estimated_cost"] else "N/A",
            f"{r['relative_cost']}x" if isinstance(r["relative_cost"], float) else "N/A",
        ]
        for r in results
    ]
    print(format_table(headers, rows, "llrrlr"))
    print()

    # Key insight callout
    print("Key Insight: SPL makes cost visible BEFORE execution via EXPLAIN.")
    print("No other prompt management framework provides this capability.")
    print()

    # Cost range
    if len(costs) >= 2:
        print(f"Cost range: ${min(costs):.4f} - ${max(costs):.4f} ({max(costs)/min(costs):.0f}x difference)")
        print(f"Choosing the right model can save up to {(1 - min(costs)/max(costs)) * 100:.0f}% per query.")

    path = save_results("experiment3_cost_estimation", results)
    print(f"\nResults saved to: {path}")

    return results


if __name__ == "__main__":
    run()
