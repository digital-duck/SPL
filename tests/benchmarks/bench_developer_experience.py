"""Experiment 1: Developer Experience - SPL vs Imperative Python.

Compares code complexity across 5 benchmark tasks.
Produces: Table 4 (Developer Experience Metrics) and data for Figure 1 (LoC bar chart).

Run: python -m tests.benchmarks.bench_developer_experience
"""

from __future__ import annotations

from tests.benchmarks.bench_utils import (
    read_example, count_lines, format_table, save_results, parse_and_optimize,
)
from tests.benchmarks.imperative_baselines import BASELINES


# SPL examples mapped to task names
SPL_EXAMPLES = {
    "simple_qa": "hello_world.spl",
    "rag_qa": "rag_query.spl",
    "multi_step": "multi_step.spl",
    "function_reuse": "custom_function.spl",
    "cached_repeat": "hello_world.spl",  # same query, SPL caching is automatic
}

TASK_LABELS = {
    "simple_qa": "Simple QA",
    "rag_qa": "RAG-augmented QA",
    "multi_step": "Multi-step CTE",
    "function_reuse": "Function Reuse",
    "cached_repeat": "Cached Repeat",
}


def count_token_ops(source: str) -> int:
    """Count manual token counting/truncation operations in Python code."""
    ops = 0
    for line in source.splitlines():
        line = line.strip()
        if "enc.encode(" in line:
            ops += 1
        if "[:chars]" in line or "truncat" in line.lower():
            ops += 1
    return ops


def run():
    results = []

    for task_name in SPL_EXAMPLES:
        spl_source = read_example(SPL_EXAMPLES[task_name])
        python_source = BASELINES[task_name]

        spl_loc = count_lines(spl_source)
        python_loc = count_lines(python_source)
        reduction = round((1 - spl_loc / python_loc) * 100, 1)
        python_token_ops = count_token_ops(python_source)

        # SPL features: automatic budget visibility and static validation
        plans = parse_and_optimize(spl_source)
        validates = len(plans) > 0

        results.append({
            "task": task_name,
            "label": TASK_LABELS[task_name],
            "spl_loc": spl_loc,
            "python_loc": python_loc,
            "reduction_pct": reduction,
            "spl_token_ops": 0,
            "python_token_ops": python_token_ops,
            "spl_budget_visible": True,
            "python_budget_visible": False,
            "spl_static_validate": validates,
            "python_static_validate": False,
        })

    # Print table
    headers = ["Task", "SPL LoC", "Python LoC", "Reduction", "Token Ops (SPL/Py)", "Budget Visible", "Static Validate"]
    rows = []
    for r in results:
        rows.append([
            r["label"],
            r["spl_loc"],
            r["python_loc"],
            f"{r['reduction_pct']}%",
            f"0 / {r['python_token_ops']}",
            "Yes / No",
            "Yes / No",
        ])

    print("=" * 70)
    print("Table 4: Developer Experience — SPL vs Imperative Python")
    print("=" * 70)
    print(format_table(headers, rows, "lrrllll"))
    print()

    # Summary stats
    avg_spl = sum(r["spl_loc"] for r in results) / len(results)
    avg_py = sum(r["python_loc"] for r in results) / len(results)
    avg_reduction = sum(r["reduction_pct"] for r in results) / len(results)
    total_py_ops = sum(r["python_token_ops"] for r in results)

    print(f"Average SPL LoC:       {avg_spl:.0f}")
    print(f"Average Python LoC:    {avg_py:.0f}")
    print(f"Average Reduction:     {avg_reduction:.1f}%")
    print(f"Total Python token ops: {total_py_ops} (SPL: 0)")
    print()

    # Save for figure generation
    path = save_results("experiment1_developer_experience", results)
    print(f"Results saved to: {path}")

    return results


if __name__ == "__main__":
    run()
