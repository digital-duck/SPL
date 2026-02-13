# CLAUDE-prompt.md

This is the document-agent prompt used to pre-generate CLAUDE.md for this repository.
Paste this prompt into your document-agent to regenerate CLAUDE.md.

---

Please create a CLAUDE.md file at the project root for this SPL (Structured Prompt Language) project.
Analyze the codebase and produce a concise, high-signal file that will be loaded at the start of
every Claude Code session. Follow these guidelines:

1. Read the project structure, pyproject.toml, key source files (especially parser.py, lexer.py,
   optimizer.py, executor.py, adapters/, storage/), tests/, and examples/
2. Keep it concise — every line should prevent a mistake Claude would otherwise make
3. Do NOT include things Claude can infer from reading code
4. Do NOT include generic Python advice Claude already knows
5. Use the standard CLAUDE.md sections below

The file should include:

## Project overview
- One-line description: SPL is a declarative SQL-inspired query language for LLM context management
- Author: Wen Gong
- Package name: spl-lang (v0.1.0)
- Python >=3.10
- The entire engine was built in one session as a human+AI co-creation experiment

## Build and install
- How to install: pip install -e ".[dev]"
- Entry point: spl = spl.cli:main

## Testing
- Test runner: pytest tests/ -q
- How to run a single test file: python -m pytest tests/test_lexer.py (and similar for others)
- Test structure: test_lexer.py (14 tests), test_parser.py (20 tests), test_optimizer.py (6 tests)
- Total: 40 tests, all must pass
- Benchmarks: python -m tests.benchmarks.bench_developer_experience (and similar for other experiments)
- IMPORTANT: Always run pytest tests/ -q after modifying parser.py, lexer.py, analyzer.py, or optimizer.py

## CLI commands
List all spl subcommands with their arguments and purpose:
- spl init — Initialize .spl/ directory (must be run first in any new project)
- spl validate <file.spl> — Parse + validate without executing
- spl explain <file.spl> — Show execution plan (token budget breakdown)
- spl execute <file.spl> [--param k=v ...] — Execute a query
- spl memory [list|get|set|delete] [args] — Inspect/modify persistent memory store
- spl rag [add|query|count] [args] — Manage vector store documents

## Code style
- Use from __future__ import annotations in all files
- Dataclasses for AST nodes and result types
- Abstract base classes for adapter interfaces
- Case-insensitive keyword handling (SQL convention)
- Configuration uses YAML (.spl/config.yaml), NOT JSON

## Architecture (critical paths)
- Pipeline: Lexer (tokens.py, lexer.py) -> Parser (parser.py) -> Analyzer (analyzer.py) -> Optimizer (optimizer.py) -> Executor (executor.py)
- Parser is hand-written recursive descent — zero external parser dependencies (no ANTLR, no Lark, no PLY). This is intentional for research formalizeability and direct error control.
- Model names can contain hyphens (claude-sonnet-4-5) and mixed segments (gpt-4o) — parser._read_model_name() handles this
- Keywords used as identifiers: parser._expect_identifier_or_keyword() handles cases like memory.output where "output" is a keyword
- Optimizer budget algorithm (document this explicitly): reserve output_budget tokens → estimate per-item token costs → apply per-item LIMIT caps → compress proportionally if over-budget (largest items first) → order execution by (cached → memory → RAG → context). Produces ExecutionPlan with ExecutionStep objects.
- LLM Adapters: spl/adapters/claude_cli.py (dev, wraps claude CLI) and spl/adapters/openrouter.py (production, httpx). Add new providers by subclassing spl/adapters/base.LLMAdapter.
- Storage: spl/storage/memory.py (SQLite key-value) and spl/storage/vector.py (FAISS + SQLite metadata)
- All storage lives in .spl/ directory (per-project, gitignore-able — analogous to .git/)
- Runtime storage files created by spl init: .spl/config.yaml, .spl/memory.db, .spl/vectors.faiss, .spl/vectors_meta.db

## Supporting modules
List and describe each supporting module (not part of the main pipeline):
- spl/functions.py — Function registry and built-in functions
- spl/token_counter.py — Token estimation (tiktoken for OpenAI models, character estimation for others)
- spl/explain.py — Formats EXPLAIN plan output for CLI display
- spl/__init__.py — Public API: parse(), validate(), explain(), execute()

## Key design decisions
- Hand-written parser: deliberate choice for research formalizeability. Formal grammar in docs/grammar.ebnf.
- Token budget as first-class concern: the optimizer's proportional compression is central to SPL's value — declarative syntax enables automatic context-window resource management.
- Adapter pattern: OpenRouter is the production path (100+ models); Claude CLI adapter bypasses API costs during development.
- .spl/ directory: all runtime state is self-contained per project.

## Common gotchas
- IMPORTANT: The lexer tokenizes hyphens as MINUS tokens. Model names like "claude-sonnet-4-5" require special handling in the parser (_read_model_name method). When adding new syntax that involves hyphens, remember this.
- IMPORTANT: Many SQL keywords (OUTPUT, RESULT, FORMAT, etc.) can appear as identifiers in dotted names like memory.output. Use _expect_identifier_or_keyword() instead of _expect(IDENTIFIER) in these positions.
- Token counting uses tiktoken for OpenAI models, character estimation for others (see token_counter.py)
- The vector store uses a simple hash-based embedding (prototype). This is intentional for zero-dependency development — not a bug.
- FAISS requires numpy. If numpy version conflicts occur (NumPy 1.x vs 2.x), reinstall faiss-cpu.

## Key files
- Grammar specification: docs/grammar.ebnf
- Design document: docs/dev/design-v1.md
- arxiv paper: docs/paper/spl-paper.tex
- Example queries: examples/*.spl (hello_world, rag_query, multi_step, custom_function)

## Workflow
- This project has an arxiv paper (docs/paper/). Changes to the engine may need corresponding paper updates.
- Benchmark data lives in docs/paper/data/ (JSON). Figures in docs/paper/figures/ (PDF).
- Regenerate figures after benchmark changes: python -m tests.benchmarks.generate_figures
- The co-creation log (docs/dev/co-creation-log.md) documents Human+AI collaboration decisions

---
Prefix the generated file with:

```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```
