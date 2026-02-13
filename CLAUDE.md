# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPL (Semantic Prompt Language) is a SQL-inspired language for orchestrating LLM interactions. It treats LLMs as generative knowledge bases, using declarative queries with token budget management. The entire engine was built in one session as a human+AI co-creation experiment.

## Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_lexer.py
python -m pytest tests/test_parser.py
python -m pytest tests/test_optimizer.py

# Run benchmarks (no API key required)
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification

# CLI usage
spl init                                    # Initialize .spl/ directory
spl validate <file.spl>                     # Parse + validate without executing
spl explain <file.spl>                      # Show execution plan
spl execute <file.spl> [--param k=v ...]    # Execute query
spl memory [list|get|set|delete] [args]     # Memory operations
spl rag [add|query|count] [args]            # RAG operations
```

## Architecture

The pipeline has five stages:

```
Lexer → Parser → Analyzer → Optimizer → Executor
```

1. **`spl/lexer.py`** — Character-by-character scanner producing a token stream
2. **`spl/parser.py`** — Hand-written recursive descent parser producing an AST. Zero external parser dependencies (no ANTLR, Lark, PLY). This is intentional for research formalizeability.
3. **`spl/analyzer.py`** — Semantic validation, type checking, scope analysis
4. **`spl/optimizer.py`** — Token budget allocation. Treats the LLM context window as a constrained resource (analogous to disk I/O in database query planning). Generates an `ExecutionPlan` with ordered `ExecutionStep` objects. Budget algorithm: reserve output tokens → estimate per-item costs → apply LIMIT caps → compress proportionally if over-budget → order by (cached → memory → RAG → context).
5. **`spl/executor.py`** — Orchestrates context gathering (system prompt, memory, RAG, context vars), calls the LLM adapter, optionally stores results

### Supporting modules

- **`spl/adapters/`** — LLM provider adapters implementing `base.LLMAdapter`. `openrouter.py` is the production adapter (100+ models via OpenRouter.ai); `claude_cli.py` wraps the Claude Code CLI for dev use without API costs.
- **`spl/storage/`** — `memory.py` is a SQLite key-value store; `vector.py` is a FAISS vector store for RAG.
- **`spl/functions.py`** — Function registry and built-in functions
- **`spl/token_counter.py`** — Token estimation via tiktoken
- **`spl/explain.py`** — Formats EXPLAIN plan output
- **`spl/__init__.py`** — Public API: `parse()`, `validate()`, `explain()`, `execute()`

### Runtime storage (per project)

Created by `spl init` under `.spl/`:
- `config.yaml` — Adapter and model configuration, token budget defaults
- `memory.db` — SQLite key-value persistent memory
- `vectors.faiss` + `vectors_meta.db` — FAISS vector index and metadata

## Key Design Decisions

- **Hand-written parser**: Deliberate choice for research purposes (formalizable grammar, direct error control). The formal grammar lives in `docs/grammar.ebnf`.
- **Token budget as first-class concern**: The optimizer's proportional compression algorithm is central to SPL's value proposition — automatic resource management that SQL-style declarative syntax enables.
- **Adapter pattern for LLMs**: Add new providers by subclassing `spl/adapters/base.LLMAdapter`. OpenRouter is the production path; Claude CLI adapter bypasses API costs during development.
- **`.spl/` directory**: All runtime state is self-contained per project, analogous to `.git/`.
