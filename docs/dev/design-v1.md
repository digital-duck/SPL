# SPL Engine - Design Document v1.0

**Date**: February 12, 2026
**Authors**: Wen Gong (vision, architecture) + Claude Opus 4.6 (implementation, synthesis)
**Status**: Prototype Development

---

## 1. Vision

SPL (Structured Prompt Language) is a declarative, SQL-inspired language for LLM context management. It treats LLMs as **generative knowledge bases** - not just passive data stores, but active systems that can synthesize new content.

**The Core Parallel**:

| Era | Problem | Solution | Impact |
|-----|---------|----------|--------|
| 1970 | Database chaos | SQL | 56 years of dominance |
| 2026 | LLM prompt chaos | SPL | Next 50 years? |

**Why SQL succeeded**: Declarative, optimizable, composable, portable, accessible.
**Why SPL can succeed**: Same principles applied to LLM context as a constrained resource.

### LLM as Generative Knowledge Base

The key insight distinguishing SPL from mere "prompt templates":

| | SQL | SPL |
|---|---|---|
| Knowledge base | Static (rows/tables) | Generative (trained weights) |
| Query result | Retrieved data | Synthesized content |
| Resource | Disk/RAM | Token budget (context window) |
| Optimization | Minimize I/O | Minimize tokens, maximize relevance |
| `SELECT` | Retrieves existing data | Gathers context |
| N/A | N/A | `GENERATE` creates new content from context |

### Real-World Inspiration: Data-Copilot

SPL grew directly out of hands-on pain encountered while building
**[Data-Copilot](https://github.com/digital-duck/data-copilot)**, a RAG-powered
conversational analytics application developed prior to SPL.

Data-Copilot's implementation exposed the recurring friction that SPL is designed
to eliminate:

| Pain point in Data-Copilot | SPL solution |
|-----------------------------|-------------|
| Manual `tiktoken` calls scattered across modules to fit prompts in context | `WITH BUDGET` + `LIMIT` clauses — the optimizer handles allocation |
| Ad hoc string concatenation to assemble prompts from retrieved chunks | `SELECT` from typed context sources with uniform syntax |
| No visibility into which chunks consumed how many tokens | `EXPLAIN` shows the full token allocation tree before execution |
| Retrieval, caching, and LLM calls wired together imperatively | Declarative `PROMPT` query — the engine handles ordering and caching |
| Provider-specific code paths (OpenAI, Claude, local Ollama) | Adapter interface — swap providers without touching query logic |

The key insight crystallised during that project: the repeated pattern of
*gather context → fit within a limit → synthesise an answer* is essentially a
**database query** — and deserved the same declarative treatment that SQL gave to
*scan rows → filter → aggregate*. Data-Copilot was the working proof that the
problem was real and worth solving at the language level.

---

## 2. Architecture

```
SPL Source (.spl file)
       |
   [Lexer]          tokens.py, lexer.py
       |
   Token Stream
       |
   [Parser]          parser.py (recursive descent)
       |
   AST              ast_nodes.py
       |
   [Analyzer]        analyzer.py
       |
   Validated AST
       |
   [Optimizer]       optimizer.py
       |
   Execution Plan
       |
   [Executor]        executor.py
   /    |    \
  /     |     \
[LLM]  [Memory] [RAG]
  |       |       |
OpenRouter SQLite  FAISS
or Claude  (.spl/  (.spl/
CLI       memory.db) vectors.faiss)
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Parser | Hand-written recursive descent | Zero deps, full control, formalizable grammar for paper |
| LLM (production) | OpenRouter.ai | Single API, 100+ models, provider-agnostic |
| LLM (development) | Claude Code CLI wrapper | Subscription billing, zero marginal cost |
| Structured storage | SQLite | File-based, portable, zero-config, battle-tested |
| Vector store | FAISS | File-based, portable, fast, widely used |
| Storage location | `.spl/` directory | Per-project, gitignore-able, self-contained |

---

## 3. SPL Syntax Specification

### 3.1 PROMPT Statement

```sql
PROMPT <name>
WITH BUDGET <n> tokens
USING MODEL <model_name>
[CACHE FOR <duration>]

SELECT
    system_role(<description>),
    context.<source> AS <alias> LIMIT <n> tokens,
    rag.query(<query>, top_k=<n>) AS <alias> LIMIT <n> tokens,
    memory.get(<key>) AS <alias> LIMIT <n> tokens

[WHERE <conditions>]
[ORDER BY <field> [ASC|DESC]]

GENERATE
    <function>(<args>)
[WITH OUTPUT BUDGET <n> tokens]
[WITH TEMPERATURE <value>]
[WITH FORMAT <format>];
```

### 3.2 WITH Clause (CTEs)

```sql
WITH <alias> AS (
    SELECT <fields>
    FROM <source>
    [WHERE <conditions>]
    [LIMIT <n> tokens]
),
<alias2> AS (...)

SELECT ...
```

### 3.3 CREATE FUNCTION

```sql
CREATE FUNCTION <name>(<params>)
RETURNS <type>
AS $$
    SELECT ...
    LIMIT <n> tokens
$$;
```

### 3.4 EXPLAIN

```sql
EXPLAIN PROMPT <name>;
```

Output shows: token allocation tree, compression decisions, cache status, estimated cost.

### 3.5 Memory Operations

```sql
STORE RESULT IN memory.<key>;
```

### 3.6 Execute with Parameters

```sql
EXECUTE PROMPT <name> WITH PARAMS (
    context.<source> = @<variable>,
    ...
);
```

---

## 4. Formal Grammar (EBNF)

See `docs/grammar.ebnf` for the complete formal grammar specification.

---

## 5. Token Types

```
Keywords:       PROMPT, WITH, BUDGET, TOKENS, USING, MODEL, SELECT, AS,
                LIMIT, WHERE, AND, OR, NOT, IN, ORDER, BY, ASC, DESC,
                GENERATE, OUTPUT, CREATE, FUNCTION, RETURNS, EXPLAIN,
                EXECUTE, PARAMS, STORE, RESULT, CACHE, FOR, FROM,
                TEMPERATURE, FORMAT

Built-ins:      SYSTEM_ROLE, CONTEXT, RAG, MEMORY

Literals:       INTEGER, FLOAT, STRING, IDENTIFIER

Operators:      DOT(.), COMMA(,), LPAREN((), RPAREN()), EQ(=), NEQ(!=),
                GT(>), LT(<), GTE(>=), LTE(<=), STAR(*), PLUS(+), MINUS(-)

Delimiters:     SEMICOLON(;), DOLLAR_DOLLAR($$)

Special:        EOF
```

---

## 6. Storage Architecture

### 6.1 `.spl/` Directory

```
.spl/
├── config.yaml          # Adapter config, API keys reference
├── memory.db            # SQLite: structured key-value store
├── vectors.faiss        # FAISS: vector similarity index
├── vectors_meta.db      # SQLite: document metadata for FAISS
└── functions/           # User-defined function files
```

### 6.2 SQLite Schema (memory.db)

```sql
CREATE TABLE kv_store (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prompt_cache (
    prompt_hash TEXT PRIMARY KEY,
    result TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

### 6.3 SQLite Schema (vectors_meta.db)

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    metadata JSON,
    embedding_model TEXT,
    tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. LLM Adapter Interface

```python
class LLMAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult: ...

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int: ...

    @abstractmethod
    def list_models(self) -> list[str]: ...

@dataclass
class GenerationResult:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float | None
```

### 7.1 OpenRouter Adapter (Production)

- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Auth: `OPENROUTER_API_KEY` env var
- Supports 100+ models through unified API

### 7.2 Claude CLI Adapter (Development)

- Wraps `claude -p "<prompt>"` via subprocess
- Zero marginal cost (subscription billing)
- Token counting via character estimation (~4 chars/token)

---

## 8. Optimizer Strategy

### Token Budget Allocation Algorithm

1. **Reserve** output budget from total budget
2. **Estimate** token cost for each SELECT item
3. **Apply** per-item LIMIT caps
4. **If over budget**: compress proportionally, largest items first
5. **Order execution**: cached items first, then memory, then RAG, then context
6. **Generate** ExecutionPlan with step-by-step operations

### EXPLAIN Output Format

```
Execution Plan for: onboarding_guide
========================================================
Budget: 8000 tokens | Model: claude-sonnet-4-5

Token Allocation:
+-- System Role           120 tokens   (1.5%)
+-- user_profile          500 tokens   (6.3%)  [compressed 75%]
+-- mentor_data          1000 tokens  (12.5%)  [compressed 67%]
+-- rag_docs             2000 tokens  (25.0%)  [cache HIT]
+-- progress              300 tokens   (3.8%)  [from memory]
+-- Task/Generate         880 tokens  (11.0%)
+-- Output Budget        3000 tokens  (37.5%)
+-- Buffer                200 tokens   (2.5%)
                         ----------
Total                    8000 tokens (100.0%)

Estimated Cost: $0.04 | Estimated Latency: 3.2s
```

---

## 9. CLI Interface

```bash
spl init                                    # Initialize .spl/ directory
spl validate <file.spl>                    # Parse + validate (no execution)
spl explain <file.spl>                     # Show execution plan
spl execute <file.spl> [--param k=v ...]   # Execute query
spl memory list                             # List all memory keys
spl memory get <key>                        # Retrieve memory value
spl memory set <key> <value>                # Store memory value
spl rag add <file> [--chunk-size 500]       # Index file into vector store
spl rag query "<text>" [--top-k 5]          # Search vector store
spl config set <key> <value>                # Set configuration
```

---

## 10. Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `faiss-cpu` | Vector similarity search (RAG) | Yes |
| `numpy` | FAISS dependency | Yes |
| `httpx` | OpenRouter API calls | Yes |
| `tiktoken` | Token counting (OpenAI models) | Yes |
| `pytest` | Testing | Dev only |

Note: SQLite is Python stdlib (no extra dependency).

---

## 11. Deliverables

1. **Python Package** (`pip install spl-llm`): Working SPL engine with CLI
2. **arxiv Paper**: "Structured Prompt Language: Declarative Context Management for Large Language Models"
3. **Co-Creation Log**: Human+AI collaborative development documentation (`docs/dev/co-creation-log.md`)

---

**Document Version**: 1.0
**Next**: Implementation (bottom-up from lexer to CLI)
