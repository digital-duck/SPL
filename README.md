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
| Tied to one LLM provider | Provider-agnostic (OpenRouter) |

## Install

```bash
pip install spl-lang
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

# Built-in RAG
spl rag add my_docs.txt
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
                                                [LLM] [SQLite] [FAISS]
                                                  |       |       |
                                              OpenRouter  Memory   RAG
                                              or Claude CLI
```

**Key design decisions:**
- **Parser**: Hand-written recursive descent (zero external parser deps)
- **LLM**: OpenRouter.ai (production, 100+ models) + Claude CLI (dev, subscription billing)
- **Memory**: SQLite (file-based, portable, zero-config)
- **Vector Store**: FAISS (file-based, native RAG)
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

## Project

- **Author**: Wen Gong (20+ years Oracle/SQL experience)
- **Vision**: [SPL Design Thinking](https://github.com/digital-duck/SPL/blob/main/docs/dev/design-v1.md)
- **Co-creation**: Built via Human+AI collaboration ([log](docs/dev/co-creation-log.md))
- **License**: MIT
