"""Experiment 4: EXPLAIN Output Showcase.

Produces accurate EXPLAIN output from real SPL queries for inclusion
in the paper as Figure 4.

Run: python -m tests.benchmarks.bench_explain_showcase
"""

from __future__ import annotations

from tests.benchmarks.bench_utils import (
    read_example, parse_and_optimize, save_results,
)
from spl.explain import explain_plan


def run():
    examples = [
        ("hello_world.spl", "Simple QA"),
        ("rag_query.spl", "RAG-augmented QA"),
        ("multi_step.spl", "Multi-step CTE"),
        ("custom_function.spl", "Function Reuse"),
    ]

    all_outputs = []

    for filename, label in examples:
        source = read_example(filename)
        plans = parse_and_optimize(source)

        print("=" * 70)
        print(f"EXPLAIN: {filename} ({label})")
        print("=" * 70)

        for plan in plans:
            output = explain_plan(plan)
            print(output)
            print()

            all_outputs.append({
                "file": filename,
                "label": label,
                "prompt_name": plan.prompt_name,
                "explain_output": output,
                "total_budget": plan.total_budget,
                "output_budget": plan.output_budget,
                "input_tokens": plan.total_input_tokens,
                "buffer_tokens": plan.buffer_tokens,
                "estimated_cost": plan.estimated_cost,
                "num_steps": len(plan.steps),
                "num_optimizations": len(plan.optimizations),
                "steps": [
                    {
                        "alias": s.alias,
                        "operation": s.operation,
                        "allocated": s.allocated_tokens,
                        "compressed": s.compressed,
                        "compression_ratio": s.compression_ratio,
                        "cache_status": s.cache_status,
                        "priority": s.priority,
                    }
                    for s in plan.steps
                ],
            })

    path = save_results("experiment4_explain_showcase", all_outputs)
    print(f"Results saved to: {path}")

    return all_outputs


if __name__ == "__main__":
    run()
