# Prompt to Generate CLAUDE.md for SPL

Copy and paste the prompt below into a new Claude Code session from the SPL project root (`/home/gongai/projects/digital-duck/SPL/`). It will produce a CLAUDE.md equivalent to what `/init` would generate, but tailored with project-specific knowledge from Session 1.

---

## Prompt

```
Please create a CLAUDE-prompted.md file at the project root for this SPL (Structured Prompt Language) project. Analyze the codebase and produce a concise, high-signal file that will be loaded at the start of every Claude Code session. Follow these guidelines:

1. Read the project structure, pyproject.toml, key source files, tests, and examples
2. Keep it concise --- every line should prevent a mistake Claude would otherwise make
3. Do NOT include things Claude can infer from reading code
4. Do NOT include generic Python advice Claude already knows
5. Use the standard CLAUDE.md sections below

The file should include:

## Project overview
- One-line description: SPL is a declarative SQL-inspired query language for LLM context management
- Author: Wen Gong
- Package name: spl-llm (v0.1.0)
- Python >=3.10

## Build and install
- How to install: pip install -e ".[dev]"
- Entry point: spl = spl.cli:main

## Testing
- Test runner: pytest tests/ -q
- Test structure: test_lexer.py (14 tests), test_parser.py (20 tests), test_optimizer.py (6 tests)
- Total: 40 tests, all must pass
- Benchmarks: python -m tests.benchmarks.bench_developer_experience (and similar for other experiments)
- IMPORTANT: Always run pytest tests/ -q after modifying parser, lexer, analyzer, or optimizer

## Code style
- Use from __future__ import annotations in all files
- Dataclasses for AST nodes and result types
- Abstract base classes for adapter interfaces
- Case-insensitive keyword handling (SQL convention)
- Configuration uses YAML (.spl/config.yaml), NOT JSON

## Architecture (critical paths)
- Pipeline: Lexer (tokens.py, lexer.py) -> Parser (parser.py) -> Analyzer (analyzer.py) -> Optimizer (optimizer.py) -> Executor (executor.py)
- Parser is hand-written recursive descent --- zero external parser dependencies (no ANTLR, no Lark)
- Model names can contain hyphens (claude-sonnet-4-5) and mixed segments (gpt-4o) --- parser._read_model_name() handles this
- Keywords used as identifiers: parser._expect_identifier_or_keyword() handles cases like memory.output where "output" is a keyword
- LLM Adapters: spl/adapters/claude_cli.py (dev, wraps claude CLI) and spl/adapters/openrouter.py (production, httpx)
- Storage: spl/storage/memory.py (SQLite) and spl/storage/vector.py (FAISS + SQLite metadata)
- All storage lives in .spl/ directory (per-project, gitignore-able)

## Common gotchas
- IMPORTANT: The lexer tokenizes hyphens as MINUS tokens. Model names like "claude-sonnet-4-5" require special handling in the parser (_read_model_name method). When adding new syntax that involves hyphens, remember this.
- IMPORTANT: Many SQL keywords (OUTPUT, RESULT, FORMAT, etc.) can appear as identifiers in dotted names like memory.output. Use _expect_identifier_or_keyword() instead of _expect(IDENTIFIER) in these positions.
- Token counting uses tiktoken for OpenAI models, character estimation for others (see token_counter.py)
- The vector store uses a simple hash-based embedding (prototype). This is intentional for zero-dependency development --- not a bug.
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
```

---

## Why This Prompt Instead of /init

The `/init` command analyzes the codebase generically. This prompt produces a CLAUDE.md that includes:

1. **Parser gotchas** (hyphenated model names, keywords-as-identifiers) that were discovered and fixed during Session 1
2. **Architectural decisions** with rationale (hand-written parser, YAML not JSON, hash embeddings)
3. **Paper workflow** integration (benchmarks, figures, LaTeX)
4. **The exact test counts** and benchmark commands

A future Claude session starting with this CLAUDE.md will avoid re-discovering the bugs we already fixed today.
