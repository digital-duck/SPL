# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

SPL is a declarative SQL-inspired query language for LLM context management.

- Author: Wen Gong
- Package name: `spl-llm` (v0.1.0)
- Python >=3.10

## Build and install

```bash
pip install -e ".[dev]"
```

Entry point: `spl = spl.cli:main`

## Testing

```bash
pytest tests/ -q
```

- `test_lexer.py` — 14 tests
- `test_parser.py` — 20 tests
- `test_optimizer.py` — 6 tests
- Total: 40 tests, all must pass

```bash
# Benchmarks (no API key required)
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification
```

**IMPORTANT:** Always run `pytest tests/ -q` after modifying `parser.py`, `lexer.py`, `analyzer.py`, or `optimizer.py`.

## Code style

- Use `from __future__ import annotations` in all files
- Dataclasses for AST nodes and result types
- Abstract base classes for adapter interfaces
- Case-insensitive keyword handling (SQL convention)
- Configuration uses YAML (`.spl/config.yaml`), NOT JSON

## Architecture (critical paths)

Pipeline:

```
Lexer (tokens.py, lexer.py) -> Parser (parser.py) -> Analyzer (analyzer.py) -> Optimizer (optimizer.py) -> Executor (executor.py)
```

- Parser is hand-written recursive descent — zero external parser dependencies (no ANTLR, no Lark)
- Model names can contain hyphens (`claude-sonnet-4-5`) and mixed segments (`gpt-4o`) — `parser._read_model_name()` handles this
- Keywords used as identifiers: `parser._expect_identifier_or_keyword()` handles cases like `memory.output` where `output` is a keyword
- LLM Adapters: `spl/adapters/claude_cli.py` (dev, wraps claude CLI) and `spl/adapters/openrouter.py` (production, httpx)
- Storage: `spl/storage/memory.py` (SQLite) and `spl/storage/vector.py` (FAISS + SQLite metadata)
- All storage lives in `.spl/` directory (per-project, gitignore-able)

## Common gotchas

**IMPORTANT:** The lexer tokenizes hyphens as `MINUS` tokens. Model names like `claude-sonnet-4-5` require special handling in the parser (`_read_model_name` method). When adding new syntax that involves hyphens, remember this.

**IMPORTANT:** Many SQL keywords (`OUTPUT`, `RESULT`, `FORMAT`, etc.) can appear as identifiers in dotted names like `memory.output`. Use `_expect_identifier_or_keyword()` instead of `_expect(IDENTIFIER)` in these positions.

- Token counting uses `tiktoken` for OpenAI models, character estimation for others (see `token_counter.py`)
- The vector store uses a simple hash-based embedding (prototype). This is intentional for zero-dependency development — not a bug.
- FAISS requires numpy. If numpy version conflicts occur (NumPy 1.x vs 2.x), reinstall `faiss-cpu`.

## Key files

- Grammar specification: `docs/grammar.ebnf`
- Design document: `docs/dev/design-v1.md`
- arxiv paper: `docs/paper/spl-paper.tex`
- Example queries: `examples/*.spl` (`hello_world`, `rag_query`, `multi_step`, `custom_function`)

## Workflow

- This project has an arxiv paper (`docs/paper/`). Changes to the engine may need corresponding paper updates.
- Benchmark data lives in `docs/paper/data/` (JSON). Figures in `docs/paper/figures/` (PDF).
- Regenerate figures after benchmark changes: `python -m tests.benchmarks.generate_figures`
- The co-creation log (`docs/dev/co-creation-log.md`) documents Human+AI collaboration decisions
