"""Experiment 5: Feature Verification — verify SPL claims from the paper.

Systematically tests each feature claimed in the competitive comparison
table (Table 3) to ensure all claims are backed by working code.

Run: python -m tests.benchmarks.bench_feature_verification
"""

from __future__ import annotations
import importlib

from tests.benchmarks.bench_utils import (
    read_example, parse_and_optimize, save_results,
)


def check(name: str, test_fn) -> dict:
    """Run a feature check and return result."""
    try:
        passed = test_fn()
        status = "PASS" if passed else "FAIL"
    except Exception as e:
        status = "FAIL"
        passed = False
        name = f"{name} ({e})"
    print(f"  {'[PASS]' if passed else '[FAIL]'} {name}")
    return {"feature": name, "status": status}


def run():
    print("=" * 70)
    print("Experiment 5: Feature Verification")
    print("=" * 70)
    print()

    results = []

    # 1. Declarative syntax - parse all examples
    print("Declarative Query Language:")
    for f in ["hello_world.spl", "rag_query.spl", "multi_step.spl", "custom_function.spl"]:
        results.append(check(
            f"Parse {f}",
            lambda f=f: len(parse_and_optimize(read_example(f))) > 0
        ))

    # 2. Token budgeting
    print("\nExplicit Token Budgeting:")
    results.append(check(
        "WITH BUDGET clause parsed",
        lambda: parse_and_optimize(read_example("hello_world.spl"))[0].total_budget == 2000
    ))
    results.append(check(
        "LIMIT clause on SELECT items",
        lambda: any(
            s.limit_tokens is not None and s.limit_tokens > 0
            for s in parse_and_optimize(read_example("rag_query.spl"))[0].steps
        )
    ))
    results.append(check(
        "OUTPUT BUDGET in GENERATE",
        lambda: parse_and_optimize(read_example("hello_world.spl"))[0].output_budget == 1000
    ))

    # 3. EXPLAIN execution plan
    print("\nEXPLAIN Execution Plan:")
    from spl.explain import explain_plan
    results.append(check(
        "EXPLAIN produces tree output",
        lambda: "Token Allocation" in explain_plan(
            parse_and_optimize(read_example("hello_world.spl"))[0]
        )
    ))
    results.append(check(
        "EXPLAIN shows percentages",
        lambda: "%" in explain_plan(
            parse_and_optimize(read_example("rag_query.spl"))[0]
        )
    ))
    results.append(check(
        "EXPLAIN shows estimated cost",
        lambda: "Cost" in explain_plan(
            parse_and_optimize(read_example("rag_query.spl"))[0]
        )
    ))

    # 4. Built-in RAG
    print("\nBuilt-in RAG:")
    results.append(check(
        "rag.query() parsed in SELECT",
        lambda: any(
            s.operation == "rag_query"
            for s in parse_and_optimize(read_example("rag_query.spl"))[0].steps
        )
    ))
    results.append(check(
        "VectorStore importable",
        lambda: importlib.import_module("spl.storage.vector") is not None
    ))

    # 5. Persistent memory
    print("\nPersistent Memory:")
    results.append(check(
        "memory.get() parsed in SELECT",
        lambda: any(
            s.operation == "memory_get"
            for s in parse_and_optimize(read_example("rag_query.spl"))[0].steps
        )
    ))
    results.append(check(
        "MemoryStore importable",
        lambda: importlib.import_module("spl.storage.memory") is not None
    ))

    # 6. SQL-like CTEs
    print("\nSQL-like CTEs:")
    results.append(check(
        "WITH ... AS parsed in multi_step.spl",
        lambda: any(
            s.operation == "cte"
            for s in parse_and_optimize(read_example("multi_step.spl"))[0].steps
        )
    ))

    # 7. User-defined functions
    print("\nUser-defined Functions:")
    from spl.lexer import Lexer
    from spl.parser import Parser
    results.append(check(
        "CREATE FUNCTION parsed",
        lambda: len(Parser(Lexer(read_example("custom_function.spl")).tokenize()).parse().statements) == 2
    ))

    # 8. Provider-agnostic
    print("\nProvider-Agnostic:")
    results.append(check(
        "ClaudeCLIAdapter importable",
        lambda: importlib.import_module("spl.adapters.claude_cli") is not None
    ))
    results.append(check(
        "OpenRouterAdapter importable",
        lambda: importlib.import_module("spl.adapters.openrouter") is not None
    ))

    # 9. Automatic compression
    print("\nAutomatic Compression:")
    over_budget_query = """\
PROMPT test
WITH BUDGET 2000 tokens
SELECT
    system_role("test"),
    context.data AS data LIMIT 3000 tokens,
    context.more AS more LIMIT 3000 tokens
GENERATE response(data, more)
WITH OUTPUT BUDGET 1000 tokens;
"""
    results.append(check(
        "Over-budget triggers compression",
        lambda: len(parse_and_optimize(over_budget_query)[0].optimizations) > 0
    ))

    # 10. Zero-dependency parser
    print("\nZero-Dependency Parser:")
    results.append(check(
        "Parser works without ANTLR/Lark",
        lambda: (
            importlib.import_module("spl.parser") is not None
            and not any(
                mod in dir(importlib.import_module("spl.parser"))
                for mod in ["antlr4", "lark"]
            )
        )
    ))

    # Summary
    print()
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"Results: {passed}/{total} checks passed")
    print()

    if passed == total:
        print("ALL PAPER CLAIMS VERIFIED")
    else:
        failed = [r for r in results if r["status"] == "FAIL"]
        print("FAILED CHECKS:")
        for r in failed:
            print(f"  - {r['feature']}")

    path = save_results("experiment5_feature_verification", results)
    print(f"\nResults saved to: {path}")

    return results


if __name__ == "__main__":
    run()
