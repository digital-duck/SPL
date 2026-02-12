"""Shared utilities for SPL benchmarks."""

from __future__ import annotations
import json
from pathlib import Path

from spl.lexer import Lexer
from spl.parser import Parser
from spl.analyzer import Analyzer
from spl.optimizer import Optimizer, ExecutionPlan
from spl.explain import explain_plan


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "docs" / "paper" / "data"
FIGURES_DIR = PROJECT_ROOT / "docs" / "paper" / "figures"
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def parse_and_optimize(source: str) -> list[ExecutionPlan]:
    """Full pipeline: lex -> parse -> analyze -> optimize."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    return Optimizer().optimize(analysis)


def explain(source: str) -> str:
    """Full pipeline through EXPLAIN output."""
    plans = parse_and_optimize(source)
    return "\n\n".join(explain_plan(p) for p in plans)


def read_example(name: str) -> str:
    """Read an example .spl file."""
    path = EXAMPLES_DIR / name
    return path.read_text()


def count_lines(source: str) -> int:
    """Count non-blank, non-comment lines."""
    return sum(
        1 for line in source.strip().splitlines()
        if line.strip() and not line.strip().startswith("--")
    )


def format_table(headers: list[str], rows: list[list], alignments: str | None = None) -> str:
    """Format data as an ASCII table.

    alignments: string of 'l' (left) or 'r' (right) per column.
    """
    if not alignments:
        alignments = "l" * len(headers)

    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(cells):
        parts = []
        for i, cell in enumerate(cells):
            s = str(cell)
            if alignments[i] == "r":
                parts.append(s.rjust(widths[i]))
            else:
                parts.append(s.ljust(widths[i]))
        return "| " + " | ".join(parts) + " |"

    sep = "|-" + "-|-".join("-" * w for w in widths) + "-|"
    lines = [fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def save_results(name: str, data: dict | list) -> Path:
    """Save benchmark results as JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def load_results(name: str) -> dict | list:
    """Load benchmark results from JSON."""
    path = DATA_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)
