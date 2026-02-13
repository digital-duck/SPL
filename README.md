# SPL - Structured Prompt Language

**SQL for LLM Context Management**

SPL is a declarative, SQL-inspired language that treats LLMs as **generative knowledge bases**. Just as SQL (1970) standardized database access, SPL standardizes LLM prompt engineering with automatic token budget optimization, built-in RAG, and persistent memory.

```sql
PROMPT answer_question
WITH BUDGET 8000 tokens
USING MODEL claude-sonnet-4-5

SELECT
    system_role("You are a knowledgeable assistant"),
    context.question AS question LIMIT 200 tokens,
    rag.query("relevant docs", top_k=5) AS docs LIMIT 3000 tokens,
    memory.get("history") AS history LIMIT 500 tokens

GENERATE
    detailed_answer(question, docs, history)
WITH OUTPUT BUDGET 2000 tokens, TEMPERATURE 0.3;
```

## Why SPL?

| Before (Imperative) | After (SPL) |
|-----|-----|
| Manual token counting | `WITH BUDGET 8000 tokens` |
| Trial-and-error truncation | `LIMIT 500 tokens` (auto-compressed) |
| No visibility into allocation | `EXPLAIN PROMPT` shows full plan |
| Copy-paste prompt templates | CTEs, functions, composition |
| Tied to one LLM provider | Provider-agnostic (Ollama, OpenRouter, Claude CLI) |

## Install

```bash
# Core install
pip install spl-lang

# With ChromaDB vector store support
pip install "spl-lang[chroma]"
```

### Zero-cost quick start with Ollama

Run SPL queries entirely locally — no API key, no cost:

```bash
# 1. Install Ollama: https://ollama.ai/download
# 2. Pull a model
ollama pull llama3.2        # 2 GB, great for most tasks
ollama pull qwen2.5         # strong reasoning and code

# 3. Install SPL and run
pip install spl-lang
spl init                    # creates .spl/config.yaml — set adapter: ollama
spl execute examples/hello_world.spl
```

## Quick Start

```bash
# Initialize workspace
spl init

# Validate syntax
spl validate examples/hello_world.spl

# Show execution plan (like SQL EXPLAIN)
spl explain examples/hello_world.spl

# Execute query
spl execute examples/hello_world.spl --param question="What is Python?"

# Built-in RAG (FAISS by default, or use --backend chroma)
spl rag add my_docs.txt
spl rag add my_docs.txt --backend chroma
spl rag query "search text" --top-k 5

# Persistent memory
spl memory set user_pref "prefers Python"
spl memory get user_pref
spl memory list
```

## EXPLAIN Output

```
Execution Plan for: answer_question
============================================================
Budget: 8,000 tokens | Model: claude-sonnet-4-5

Token Allocation:
+-- __system_role__               20 tokens  (  0.2%)
+-- history                      500 tokens  (  6.2%)  [from memory]
+-- docs                       3,000 tokens  ( 37.5%)  [cache MISS]
+-- question                     200 tokens  (  2.5%)
+-- Output Budget              2,000 tokens  ( 25.0%)
\-- Buffer                     2,280 tokens  ( 28.5%)
                               ----------
Total                          5,720 / 8,000 tokens (71.5%)

Estimated Cost: $0.0412
```

## Architecture

```
SPL Source (.spl)
    |
[Lexer] -> [Parser] -> [Analyzer] -> [Optimizer] -> [Executor]
                                                    /    |    \
                                                [LLM] [SQLite] [FAISS or ChromaDB]
                                                  |       |
                                          Ollama (local)  Memory
                                          OpenRouter       RAG
                                          Claude CLI
```

**Key design decisions:**
- **Parser**: Hand-written recursive descent (zero external parser deps)
- **LLM**: Ollama (local, free) + OpenRouter.ai (production, 100+ models) + Claude CLI (dev)
- **Memory**: SQLite (file-based, portable, zero-config)
- **Vector Store**: FAISS (default) or ChromaDB (`--backend chroma`)
- **Storage**: `.spl/` directory per project

## Python API

```python
import spl

# Parse
ast = spl.parse(open("query.spl").read())

# Validate
result = spl.validate(open("query.spl").read())

# Explain
print(spl.explain(open("query.spl").read()))

# Execute
import asyncio
result = asyncio.run(spl.execute(
    open("query.spl").read(),
    params={"question": "What is Python?"}
))
print(result.content)
```

## SPL Syntax

See [docs/dev/design-v1.md](docs/dev/design-v1.md) for full syntax specification and [docs/grammar.ebnf](docs/grammar.ebnf) for formal grammar.

## Benchmark Results

SPL was evaluated across 5 experiments (all runnable without API keys):

| Metric | Result |
|--------|--------|
| Code reduction vs imperative Python | **65% average** (15 vs 44 lines of code) |
| Manual token-counting ops eliminated | **35 ops across 5 tasks** (SPL: 0) |
| Cross-model cost visibility | **68x cost difference** visible before execution |
| Feature claims verified | **20/20** automated checks pass |
| Parser test suite | **58/58** tests pass (incl. FAISS + ChromaDB storage) |

```bash
# Run benchmarks yourself
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification
```

## Session 1 Summary (Feb 12, 2026)

The entire SPL engine --- from idea to working prototype with arxiv paper --- was built in a single Human+AI co-creation session:

**What was built:**
- Complete language specification (EBNF grammar, 30+ keywords, 50+ token types)
- Full engine pipeline: Lexer, Parser (hand-written recursive descent), Semantic Analyzer, Token Budget Optimizer, Executor
- Three LLM adapters: Ollama (local, free) + OpenRouter.ai (100+ models) + Claude Code CLI (subscription billing)
- Storage layer: SQLite persistent memory + FAISS vector store + ChromaDB (native RAG)
- CLI tool with 10 commands (`spl init/validate/explain/execute/memory/rag`)
- 4 example `.spl` programs covering basic QA, RAG, CTEs, and functions
- 40 unit tests + 5 benchmark experiments + 4 paper figures
- arxiv paper draft (~12 pages) with formal grammar, evaluation data, and competitive analysis
- pip-installable package (`spl-lang v0.1.0`)

**The core insight:** The LLM context window is a constrained resource --- just like disk I/O was for databases. Constrained resources deserve declarative query languages with optimizers. This is Codd's 1970 insight applied to 2026's problem.

## Project

- **Author**: Wen Gong (20+ years Oracle/SQL experience)
- **Vision**: [SPL Design Thinking](docs/dev/design-v1.md)
- **Paper**: [arxiv draft](docs/paper/spl-paper.tex) | [figures](docs/paper/figures/) | [benchmark data](docs/paper/data/)
- **Co-creation**: Built via Human+AI collaboration ([log](docs/dev/co-creation-log.md))
- **History**: [Why SPL required interdisciplinary thinking](docs/history-lessons.md)
- **License**: Apache 2.0
