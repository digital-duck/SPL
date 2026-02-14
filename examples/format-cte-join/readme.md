# format-cte-join — Real-World Validation Suite

**Use case**: Generate a multilingual table of Chinese characters containing the radical 日 (rì),
including formula, pinyin, English meaning, Chinese explanation, German translation, and natural insight.

Inspired by the 日 Family case study in:
> Wen Gong, *Geometric Patterns of Meaning: A PHATE Manifold Analysis of Multi-lingual Embeddings*,
> arXiv:2601.09731

---

## Requirement Specification

### Input
- A Chinese radical (e.g. `日` — sun/day)

### Desired Output
A structured table in markdown format:

| Character | Formula | Pinyin | English Meaning | Chinese Explanation | German Translation | Natural Insight |
|-----------|---------|--------|----------------|--------------------|--------------------|----------------|
| 明 | 日＋月＝明 | míng | bright | 日月同辉，光明 | hell, strahlend | Sun and moon as primary celestial light sources |
| ... | ... | ... | ... | ... | ... | ... |

### Sub-tasks Required
1. Select 10 characters containing the radical, with formulas and pinyin
2. Provide English meaning and Chinese explanation
3. Translate to German (requires European language expertise)
4. Provide natural/cultural insight for each character

---

## Iteration History

### v1 — `ri_family_v1.spl` ✅ Working (SPL v0.1.0+)

**Approach**: Single PROMPT with inline GENERATE instruction. All sub-tasks handled by one LLM call.

**How it works**:
- No CREATE FUNCTION needed — instruction is a string literal inside `GENERATE ri_table(radical, "...")`
- The `{radical}` placeholder in the instruction string is substituted at execution time
- `FORMAT markdown` signals the LLM to output a markdown table

**Run with Ollama (qwen2.5 local)**:
```bash
spl execute examples/format-cte-join/ri_family_v1.spl --param radical="日"


spl execute examples/format-cte-join/ri_family_v2.spl --adapter claude_cli --param radical="日" 
spl execute examples/format-cte-join/ri_family_v2_openrouter.spl --adapter openrouter --param radical="日" 
spl execute examples/format-cte-join/ri_family_v2_ollama.spl --adapter ollama --param radical="日" 
```

**Run with OpenRouter** (set adapter in `.spl/config.yaml`):
```bash
spl execute examples/format-cte-join/ri_family_v1.spl --param radical="日"
```

**With caching enabled** (saves cost on repeat runs):
```bash
spl execute examples/format-cte-join/ri_family_v1.spl --param radical="日" --cache
```

**What to verify**:
- [ ] Output is a clean markdown table with all 7 columns
- [ ] 10 rows of Chinese characters containing 日
- [ ] Formulas are compositional (e.g. 日＋月＝明)
- [ ] Pinyin includes tone marks
- [ ] German translations are accurate
- [ ] Natural insight column is culturally meaningful

**Limitations**:
- All sub-tasks use the same model — no per-task specialization
- Single LLM must handle Chinese, German, and cultural insight simultaneously
- No parallelism — one API call, sequential

---

### v2 — `ri_family_v2.spl` ✅ Implemented (SPL v0.2)

**Approach**: Three independent CTEs dispatched to specialist models **in parallel** via
`asyncio.gather`, composed by a fourth final PROMPT.

**Execution flow**:
```
params: radical="日"
    │
    ├──[qwen2.5]──────> characters CTE  (Chinese + pinyin + English)   ──┐
    ├──[mistral]──────> german CTE       (German translations)           ──┼──> [claude-sonnet] ──> final table
    └──[llama3.1:8b]──> insights CTE    (cultural / natural insight)    ──┘
           (all 3 run in PARALLEL via asyncio.gather)          (waits for all 3, then synthesizes)
```

**Model routing**:
| CTE | Model | Reason |
|-----|-------|--------|
| `characters` | `qwen2.5` | Best CJK language model |
| `german` | `mistral` | Strong European language coverage |
| `insights` | `llama3.1:8b` | Broad encyclopedic knowledge |
| Final compose | `anthropic/claude-sonnet-4-5` | Superior structured synthesis |

> **Model name quoting**: All model names use quoted strings in `.spl` files
> (e.g. `USING MODEL "qwen2.5"`) to correctly handle slashes, dots, and colons.
> Ollama format: `"qwen2.5"`, `"mistral"`, `"llama3.1:8b"`.
> OpenRouter format: `"qwen/qwen-2.5-72b-instruct"`, `"mistralai/mistral-7b-instruct"`,
> `"meta-llama/llama-3.1-8b-instruct"`, `"anthropic/claude-sonnet-4-5"`.

**Run with Ollama** (requires qwen2.5, mistral, llama3.1:8b locally):
```bash
# Pull models first if not already available:
ollama pull qwen2.5
ollama pull mistral
ollama pull llama3.1:8b

spl execute examples/format-cte-join/ri_family_v2.spl --param radical="日"
```

**Run with OpenRouter** (update model names in the .spl file to OpenRouter IDs):
```bash
# Set in .spl/config.yaml:  default_adapter: openrouter
# Set in .spl/config.yaml:  openrouter_api_key: <your-key>
spl execute examples/format-cte-join/ri_family_v2.spl --param radical="日"
```

**With caching** (saves cost on repeat runs — recommended for testing):
```bash
spl execute examples/format-cte-join/ri_family_v2.spl --param radical="日" --cache
```

**What to verify**:
- [ ] 4 total LLM calls are made (3 CTEs + 1 final)
- [ ] CTEs 1, 2, 3 use different models (qwen2.5 / mistral / llama3.1:8b)
- [ ] Final call uses claude-sonnet (or whichever synthesis model is configured)
- [ ] Output is a clean markdown table with all columns populated
- [ ] Each CTE's JSON output feeds correctly into the final compose prompt
- [ ] `context.characters`, `context.german`, `context.insights` all resolve

---

## Cache Behavior

By default, **caching is disabled** for development. This ensures every run calls the real LLM.

| Flag | Behavior |
|------|----------|
| _(no flag)_ | Cache disabled — always calls LLM |
| `--cache` | Cache enabled — saves result, returns cached on repeat |

Cache is stored in `.spl/memory.db` (SQLite). To clear it:
```bash
rm .spl/memory.db
```

---

## Adapter Configuration (`.spl/config.yaml`)

```yaml
# For Ollama (local models, free):
default_adapter: ollama

# For OpenRouter (100+ models, paid):
default_adapter: openrouter
openrouter_api_key: "your-key-here"

# For Claude CLI (Anthropic subscription, ignores model names):
default_adapter: claude_cli
```

---

## What Was Implemented (SPL v0.2)

All executor gaps from the original v2 target are now resolved:

| Gap | Status | Implementation |
|-----|--------|----------------|
| CTE nested PROMPT parsing | ✅ Done | `parser._parse_inner_prompt()` detects `PROMPT` inside CTE parens |
| Parallel async CTE execution | ✅ Done | `executor._execute_cte_step()` + `asyncio.gather()` |
| CTE result stored as `context.<name>` | ✅ Done | `context_parts[step.alias] = result.content` |
| Per-CTE `USING MODEL` dispatch | ✅ Done | Sub-plan uses `cte_stmt.model` for each CTE call |
| String literal instructions in GENERATE | ✅ Done | `_assemble_prompt` extracts Literal args, substitutes `{param}` |
| Cache off by default | ✅ Done | `Executor(cache_enabled=False)` is default; `--cache` flag to enable |

**Key AST/optimizer changes**:
- `CTEClause.nested_prompt: PromptStatement | None` — stores the nested PROMPT
- `ExecutionStep.cte_stmt: object` — carries the nested PROMPT to the executor

---

## The Bigger Vision: SPL as Multi-Model Orchestration Layer

### The MapReduce Analogy

| Big Data (2004) | SPL Multi-Model (2026) |
|----------------|----------------------|
| MapReduce paper (Google) | SPL parallel CTE execution |
| Commodity hardware cluster | 100+ models via OpenRouter |
| Map: parallel data processing | CTEs: parallel specialist LLM calls |
| Reduce: aggregate results | Final PROMPT: compose CTE responses |
| Declarative (Hive/Pig SQL) | Declarative SPL syntax |
| Input: distributed data shards | Input: sub-problem decomposition |
| Output: aggregated dataset | Output: composed LLM response |

**Model specialization is real.** No single LLM is best at everything:
- Qwen2.5 outperforms others on Chinese/Japanese/Korean tasks
- Mistral leads on European languages
- Code-specific models (deepseek-coder, codellama) outperform on programming tasks
- Large frontier models (claude, gpt-4) are best at synthesis and reasoning

**Cost implication**: A complex task costing ~$0.04 with claude-sonnet alone
costs ~$0.014 with three specialized smaller models routed via SPL CTEs,
with equal or better quality on each sub-task.

This is the same breakthrough as MapReduce: **move from one expensive generalist
doing everything sequentially, to many specialized resources coordinated declaratively.**

---

## Files

| File | Status | Description |
|------|--------|-------------|
| `ri_family_v1.spl` | ✅ Working | Single PROMPT, one model, inline instruction |
| `ri_family_v2.spl` | ✅ Implemented | Multi-model parallel CTEs + final synthesis |
| `readme.md` | This file | Spec, run instructions, verification checklist |

---

*Last updated: February 2026 — SPL v0.2 CTE execution implemented.*
