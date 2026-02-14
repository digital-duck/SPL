# SPL User Guide

**Structured Prompt Language — Declarative Context Management for LLMs**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Your First SPL Query](#your-first-spl-query)
5. [SPL Syntax Reference](#spl-syntax-reference)
6. [CLI Commands](#cli-commands)
7. [LLM Adapters](#llm-adapters)
8. [Vector Store (RAG)](#vector-store-rag)
9. [Persistent Memory](#persistent-memory)
10. [EXPLAIN — Inspect Execution Plans](#explain--inspect-execution-plans)
11. [Python API](#python-api)
12. [Examples](#examples)

---

## Prerequisites

- Python 3.10 or later
- At least one of the following LLM backends:
  - **Ollama** (recommended for beginners — free, local, no API key)
  - **OpenRouter** account + API key (production, 100+ cloud models)
  - **Claude Code CLI** (Anthropic subscription)

---

## Installation

```bash
# Core install
pip install spl-llm

# With ChromaDB vector store support
pip install "spl-llm[chroma]"

# Development install (from source)
git clone https://github.com/digital-duck/SPL
cd SPL
pip install -e ".[dev]"
```

---

## Configuration

Initialize a workspace in your project directory:

```bash
spl init
```

This creates `.spl/config.yaml`. Edit it to select your LLM backend:

### Option A — Ollama (local, free, recommended for getting started)

```yaml
adapter: ollama
model: llama3.2          # or qwen2.5, mistral, gemma2, deepseek-coder-v2, etc.
ollama_base_url: http://localhost:11434   # change for remote Ollama server
token_budget: 8000
output_budget: 2000
```

Install Ollama and pull a model first:

```bash
# Install: https://ollama.ai/download
ollama pull llama3.2          # 2 GB — fast, general purpose
ollama pull qwen2.5           # strong reasoning and code
ollama pull mistral           # 7B, good balance
ollama pull deepseek-coder-v2 # code-focused tasks
ollama pull gemma2            # Google Gemma 2 9B

# Start the server (auto-started on most systems after install)
ollama serve

# Verify
ollama list
```

### Option B — OpenRouter (cloud, 100+ models)

```yaml
adapter: openrouter
model: anthropic/claude-sonnet-4-5
token_budget: 8000
output_budget: 2000
```

```bash
export OPENROUTER_API_KEY=sk-or-...
```

### Option C — Claude CLI (Anthropic subscription)

```yaml
adapter: claude_cli
model: claude-sonnet-4-5
token_budget: 8000
output_budget: 2000
```

---

## Your First SPL Query

Create `hello.spl`:

```sql
PROMPT greet
WITH BUDGET 2000 tokens
USING MODEL llama3.2

SELECT
    system_role("You are a friendly assistant."),
    context.name AS name LIMIT 50 tokens

GENERATE
    greeting(name)
WITH OUTPUT BUDGET 500 tokens;
```

Run it:

```bash
spl validate hello.spl               # check syntax
spl explain hello.spl                # preview token allocation
spl execute hello.spl --param name="Wen"
```

---

## SPL Syntax Reference

### Basic structure

```sql
PROMPT <query_name>
[WITH BUDGET <n> tokens]
[USING MODEL <model_name>]

SELECT
    <context_item> [AS <alias>] [LIMIT <n> tokens],
    ...

GENERATE
    <output_fn>(<args>)
[WITH OUTPUT BUDGET <n> tokens]
[, TEMPERATURE <float>]
[, FORMAT <format>];
```

### Context sources

| Source | Syntax | Description |
|--------|--------|-------------|
| System role | `system_role("text")` | LLM persona/instructions |
| Variable | `context.<name> AS alias` | Runtime parameter |
| RAG | `rag.query("query", top_k=5) AS alias` | Vector similarity search |
| Memory | `memory.get("key") AS alias` | Persistent key-value store |

### LIMIT

Cap token usage per item:

```sql
SELECT
    rag.query("docs") AS docs LIMIT 3000 tokens,
    memory.get("history") AS history LIMIT 500 tokens
```

### CTEs (Common Table Expressions)

Compose queries from reusable named results:

```sql
WITH summary AS (
    PROMPT summarize ...
),
analysis AS (
    PROMPT analyze
    SELECT context.summary AS s ...
)
PROMPT final_answer
SELECT context.analysis AS a ...
```

### User-defined functions

```sql
CREATE FUNCTION qa(question, docs) AS
    "Answer {question} using only information from: {docs}"
;
```

### WHERE clause

Filter RAG results:

```sql
SELECT
    rag.query("python tutorial") AS docs
    WHERE docs.source = "official_docs"
    ORDER BY docs.score ASC
    LIMIT 2000 tokens
```

### EXPLAIN

Preview execution plan without running the LLM:

```sql
EXPLAIN PROMPT my_query
WITH BUDGET 8000 tokens
...
```

---

## CLI Commands

### `spl init`
Initialize `.spl/` workspace directory.
```bash
spl init
```

### `spl validate`
Parse and validate syntax — no LLM call.
```bash
spl validate query.spl
```

### `spl explain`
Show token allocation plan — no LLM call.
```bash
spl explain query.spl
spl explain query.spl --param question="What is Python?"
```

### `spl execute`
Run a query against the configured LLM.
```bash
spl execute query.spl
spl execute query.spl --param question="What is Python?" --param lang="English"
```

### `spl rag`
Manage the vector store for RAG.
```bash
# Add documents (FAISS by default)
spl rag add docs.txt
spl rag add docs.txt --backend chroma

# Search
spl rag query "your search text" --top-k 5
spl rag query "your search text" --backend chroma

# Count indexed documents
spl rag count
spl rag count --backend chroma
```

### `spl memory`
Manage persistent key-value memory.
```bash
spl memory set key "value"
spl memory get key
spl memory list
spl memory delete key
```

---

## LLM Adapters

SPL ships with three adapters. All implement the same interface.

### Ollama (local, free)

```python
from spl.adapters import get_adapter

adapter = get_adapter("ollama", default_model="llama3.2")
# or connect to a remote Ollama server:
adapter = get_adapter("ollama",
    base_url="http://192.168.1.10:11434",
    default_model="qwen2.5"
)
```

List installed models:
```python
print(adapter.list_models())   # queries your local Ollama instance
```

**Tested models** (from the screenshot above):
| Model | Size | Best for |
|-------|------|---------|
| `llama3.2` | 2 GB | General Q&A, fast |
| `llama3` | 4.7 GB | Higher quality general tasks |
| `qwen2.5` | 1.9 GB (3b) | Reasoning, multilingual |
| `gemma2` | 5.4 GB | Instruction following |
| `deepseek-coder-v2` | 8.9 GB | Code generation |

### OpenRouter (100+ cloud models)

```python
adapter = get_adapter("openrouter", api_key="sk-or-...")
```

### Claude CLI (Anthropic subscription)

```python
adapter = get_adapter("claude_cli")
```

---

## Vector Store (RAG)

SPL supports two vector store backends with an identical interface.

### FAISS (default — file-based, zero config)

```bash
spl rag add document.txt
spl rag query "search query" --top-k 3
```

Files created: `.spl/vectors.faiss`, `.spl/vectors_meta.db`

### ChromaDB (install: `pip install "spl-llm[chroma]"`)

```bash
spl rag add document.txt --backend chroma
spl rag query "search query" --backend chroma --top-k 3
```

Files created: `.spl/chroma/`

ChromaDB uses `all-MiniLM-L6-v2` embeddings by default (requires `sentence-transformers`),
which gives significantly better retrieval quality than FAISS's hash-based default embedding.

### Python API

```python
from spl.storage import get_vector_store

store = get_vector_store("faiss", ".spl")   # or "chroma"
store.add("Python is a high-level language.", {"source": "wiki"})
results = store.query("programming language", top_k=3)
for r in results:
    print(r["text"], r["score"])
store.close()
```

---

## Persistent Memory

Memory is a SQLite-backed key-value store under `.spl/memory.db`.

```bash
# CLI
spl memory set session_context "user is an expert in Python"
spl memory get session_context
spl memory list
spl memory delete session_context
```

```python
from spl.storage.memory import MemoryStore

mem = MemoryStore(".spl/memory.db")
mem.set("pref", "concise answers")
print(mem.get("pref"))
```

In SPL queries:
```sql
SELECT memory.get("session_context") AS context LIMIT 500 tokens
```

---

## EXPLAIN — Inspect Execution Plans

`spl explain` shows the full token allocation plan without calling the LLM.
Use it to tune your budget before spending tokens.

```bash
spl explain examples/hello_world.spl
```

Example output:
```
Execution Plan for: answer_question
============================================================
Budget: 8,000 tokens | Model: llama3.2

Token Allocation:
+-- __system_role__               20 tokens  (  0.2%)
+-- history                      500 tokens  (  6.2%)  [from memory]
+-- docs                       3,000 tokens  ( 37.5%)  [cache MISS]
+-- question                     200 tokens  (  2.5%)
+-- Output Budget              2,000 tokens  ( 25.0%)
\-- Buffer                     2,280 tokens  ( 28.5%)
                               ----------
Total                          5,720 / 8,000 tokens (71.5%)

Estimated Cost: $0.00  (Ollama — local inference)
```

---

## Python API

```python
import asyncio
import spl

source = open("query.spl").read()

# Parse only
ast = spl.parse(source)

# Validate (returns warnings/errors without executing)
result = spl.validate(source)
print(result)

# Show execution plan
print(spl.explain(source))

# Execute
result = asyncio.run(spl.execute(
    source,
    params={"question": "What is Python?"},
    adapter_name="ollama",     # or "openrouter", "claude_cli"
    vector_backend="faiss",    # or "chroma"
))
print(result.content)
print(f"Tokens: {result.total_tokens} | Latency: {result.latency_ms:.0f}ms | Cost: ${result.cost_usd:.4f}")
```

---

## Examples

The `examples/` directory contains ready-to-run `.spl` files:

| File | Description |
|------|-------------|
| `hello_world.spl` | Basic PROMPT/SELECT/GENERATE |
| `rag_query.spl` | RAG with WHERE/ORDER BY |
| `multi_step.spl` | CTEs and query composition |
| `custom_function.spl` | User-defined functions |

Run any example:
```bash
spl explain examples/rag_query.spl
spl execute examples/hello_world.spl --param question="What is recursion?"
```

---

## Troubleshooting

**`Cannot connect to Ollama`**
```bash
ollama serve          # start the server
ollama list           # verify models are installed
ollama pull llama3.2  # pull a model if none installed
```

**`OPENROUTER_API_KEY not set`**
```bash
export OPENROUTER_API_KEY=sk-or-your-key-here
```

**FAISS numpy conflict**
```bash
pip install --force-reinstall faiss-cpu
```

**ChromaDB rejects empty metadata**
This is handled automatically by `ChromaStore._clean_meta()` — pass `None` or a non-empty dict.

---

## Further Reading

- [Language Design](docs/dev/design-v1.md) — full syntax spec and design decisions
- [Formal Grammar](docs/grammar.ebnf) — EBNF specification
- [arXiv Paper](docs/paper/spl-paper.tex) — research paper with benchmarks
- [Co-creation Log](docs/dev/co-creation-log.md) — Human+AI development journal
