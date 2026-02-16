# Use Case 2: Recent Papers by Top Prize Winners

**File**: `papers-by-top-prize-winners-recently_v1.spl`
**Date**: February 2026
**Status**: Ready to run / BENCHMARK-ready

---

## The Original Question

> *"List the most recent 2 papers published by Nobel Prize winners in Physics,
> Fields Medal winners in Mathematics, and Turing Award winners in Computer
> Science in the last 5 years. I am going to ask the same question to ChatGPT,
> Gemini, and Claude, and see how each response compares."*

A deceptively simple question. One sentence. Three domains. Three AI systems.
And a surprisingly rich set of design decisions hiding underneath.

---

## Why This Is an Interesting Test Case

### It Is Simultaneously a Knowledge Problem and a Search Problem

| Lens | What it means |
|------|--------------|
| **Knowledge problem** | The model must know who the recent prize winners are, and what they published *after* winning — facts encoded in its training data |
| **Search problem** | Finding the *most recent* papers requires up-to-date retrieval; a knowledge cutoff of mid-2024 may miss 2024–2025 publications |

This duality makes it a natural benchmark:
- **LLMs with web search** (Google Gemini, ChatGPT with browsing) have a structural advantage on recency
- **LLMs without search** must rely on training data — and may confidently cite papers that don't exist
- **The gap between these two behaviours** is the most interesting comparison dimension

### It Probes Honesty Under Uncertainty

Prize winners are famous people. Models know their names and general research areas.
This creates the worst condition for hallucination: *the model knows enough to sound
authoritative, but not enough to be accurate on specific paper titles and journals.*

A well-calibrated model should say *"I am not certain of this title — please verify."*
An overconfident model will invent a plausible-sounding paper with full bibliographic
detail, none of which checks out on Google Scholar.

**The system role instruction in the SPL query is the key instrument here:**

```
"Provide accurate, verifiable information only.
If you are not certain of a specific paper title, journal, or year,
say so explicitly rather than guessing — factual accuracy matters
more than completeness."
```

This instruction does not eliminate hallucination, but it raises the cost of
fabrication. The model must actively choose to ignore the instruction in order
to confabulate — and different models respond to this differently.

---

## The Declarative Insight

The user's question is entirely *declarative*:

> **What**: the 2 most recent papers, per domain, per prize type
> **Who**: Nobel (Physics), Fields (Math), Turing (CS)
> **When**: last 5 years (2020–2025)
> **How**: irrelevant — the user does not care

This is the core value proposition of SPL. In a traditional approach, a developer
would write imperative code:

```python
# Imperative approach (without SPL)
for domain in ["physics", "mathematics", "cs"]:
    model = pick_model(domain)           # manual routing decision
    prompt = build_prompt(domain)        # manual string assembly
    tokens = count_tokens(prompt)        # manual token counting
    if tokens > limit:
        prompt = truncate(prompt)        # manual truncation
    response = call_llm(model, prompt)   # manual API call
    results.append(parse(response))      # manual parsing
```

With SPL, the same intent is expressed as a query:

```sql
PROMPT physics_prize_papers
WITH BUDGET 4000 tokens
USING MODEL auto          -- routing handled by SPL

SELECT
    system_role("..."),
    context.years AS time_window LIMIT 50 tokens

GENERATE
    list_recent_papers("List the 2 most recent papers ...")
WITH OUTPUT BUDGET 1200 tokens, TEMPERATURE 0.1, FORMAT markdown;
```

The developer declares *what* they want. SPL handles *how* to get it:
token allocation, model routing, output formatting, budget enforcement.

This is the same leap SQL made in 1970: from navigational (tell the database
*how* to find the data) to declarative (tell the database *what* data you need).

---

## SPL Design Decisions

### Three PROMPT Statements, Not One

One could ask all three questions in a single `GENERATE` call. Instead the query
uses three separate `PROMPT` statements — one per domain.

**Why:**
- Cleaner per-domain output (each section is independently formatted)
- Independent token budgets (each domain gets 1,200 output tokens)
- `USING MODEL auto` routes each domain independently — a physics-specialist
  model handles physics, a math-specialist handles math
- Easier to compare per-domain quality across models in the BENCHMARK

### `USING MODEL auto` — Mixture-of-Models Routing

Rather than hard-coding `USING MODEL "anthropic/claude-sonnet-4-5"`, each PROMPT
uses `USING MODEL auto`. The SPL router classifies the task at execution time and
dispatches to the world's best specialist for that category.

For general knowledge/research tasks like this one, the routing table would
typically resolve to the current frontier reasoning model. But for a multi-domain
query spanning physics equations, mathematical proofs, and CS systems — a future
routing table might send each to a different specialist.

**This is the AI Symphony**: multiple voices, each playing their part on cue,
coordinated by the declarative structure of the query — not by imperative
orchestration code.

### `TEMPERATURE 0.1` — Factual Mode

Standard creative temperature (0.7–1.0) is designed for variety and fluency.
For factual recall, it actively worsens accuracy: the model explores a wider
space of plausible-sounding completions, many of which are fabricated.

`TEMPERATURE 0.1` keeps the model close to its highest-probability completions —
the facts it is most confident about. This does not eliminate hallucination, but
it significantly reduces it for citation-type queries.

### `FORMAT markdown` — Structured Comparison

The table format (`| Winner | Award year | Paper title | Journal | Pub. year | Summary |`)
makes human verification easy: open Google Scholar, paste the title, check.
It also makes automated verification possible in a future pipeline.

---

## The BENCHMARK: Comparing ChatGPT, Gemini, and Claude

SPL's `BENCHMARK` construct runs the same `.spl` file against a list of models
in parallel (`asyncio.gather`) and returns a structured JSON report.

```bash
# Via CLI (OpenRouter — requires OPENROUTER_API_KEY)
spl benchmark examples/format-cte-join/papers-by-top-prize-winners-recently_v1.spl \
    --model anthropic/claude-sonnet-4-5 \
    --model openai/gpt-4o              \
    --model google/gemini-pro-1.5      \
    --adapter openrouter               \
    --json > prize_papers_comparison.json

# Via SPL-Flow Streamlit UI
# → Page 3 (Benchmark) → paste SPL → select models → Run
```

**What to look for in the comparison:**

| Signal | Interpretation |
|--------|---------------|
| All three models cite the same paper | High-confidence ground truth — verify anyway |
| Two agree, one differs | Minority is likely hallucinating |
| All three cite different papers | Low reliability — search required |
| Model hedges ("I'm not certain of this title") | Good calibration, follows system role |
| Model gives full citation with no hedging | Verify carefully — may be confabulated |
| Model refuses ("my knowledge cutoff is...") | Honest but unhelpful — a different failure mode |
| Google Search returns the paper | Ground truth verification |

**The most important comparison is not *what* each model says, but *how confident*
it is when it shouldn't be.** That tells you more about production reliability than
any benchmark score.

---

## The Full SPL Query

```sql
-- papers-by-top-prize-winners-recently_v1.spl
-- 2 most recent papers by Nobel (Physics) / Fields (Math) / Turing (CS) winners
-- Last 5 years: 2020–2025

-- ── Domain 1: Nobel Prize in Physics ─────────────────────────
PROMPT physics_prize_papers
WITH BUDGET 4000 tokens
USING MODEL auto

SELECT
    system_role("You are a scholarly research assistant specialising in physics.
Provide accurate, verifiable information only. If you are not certain of a
specific paper title, journal, or year, say so explicitly rather than
guessing — factual accuracy matters more than completeness."),
    context.years AS time_window LIMIT 50 tokens

GENERATE
    list_recent_papers(
        "List the 2 most recent research papers (2020-2025) authored or
co-authored by Nobel Prize winners in Physics. For each entry:
| Prize winner | Nobel year | Paper title | Journal | Pub. year | 1-sentence summary |
Cite only papers you are confident exist."
    )
WITH OUTPUT BUDGET 1200 tokens, TEMPERATURE 0.1, FORMAT markdown;

-- ── Domain 2: Fields Medal in Mathematics ────────────────────
PROMPT math_prize_papers
WITH BUDGET 4000 tokens
USING MODEL auto
-- ... (same structure, math domain)

-- ── Domain 3: Turing Award in Computer Science ───────────────
PROMPT cs_prize_papers
WITH BUDGET 4000 tokens
USING MODEL auto
-- ... (same structure, CS domain)
```

See the full query in `papers-by-top-prize-winners-recently_v1.spl`.

---

## Broader Implications

### SPL as a Thinking Tool

Writing this query in SPL forced explicit decisions that an ad hoc ChatGPT
prompt does not:

- What is the token budget? (`WITH BUDGET 4000 tokens`)
- How should uncertainty be handled? (system role instruction)
- What temperature is appropriate for this task? (`TEMPERATURE 0.1`)
- Should domains be separated? (three `PROMPT` statements vs one)
- Which model is best for this task? (`USING MODEL auto`)

These are good engineering questions. SPL makes them unavoidable — not as
bureaucratic overhead, but as a natural consequence of writing a query.

### The Search vs. Knowledge Duality

This use case also points to a future direction: SPL's `rag.query()` source
could be connected to a web search tool, turning the query into:

```sql
SELECT
    system_role("..."),
    rag.query("Nobel Prize Physics 2024 winner papers", top_k=5) AS search_results
        LIMIT 2000 tokens
```

When the knowledge question becomes a retrieval question, SPL's architecture
handles it seamlessly — same syntax, different data source. The declarative
layer remains unchanged; only the adapter changes.

---

## Medium Blog Angle

**Proposed title**: *"I Asked ChatGPT, Gemini, and Claude the Same Question About Nobel Prize Winners — Here's What SPL Revealed"*

**Hook**: A single sentence question exposed three different failure modes in three leading AI systems — and a new query language made the comparison reproducible.

**Structure**:
1. The question (simple, relatable)
2. The naive approach (just ask ChatGPT) — and what goes wrong
3. Why this is hard (knowledge cutoff + hallucination + no structured output)
4. The SPL approach — what changes when you write a *query* instead of a *prompt*
5. The BENCHMARK results — side-by-side comparison table
6. The deeper point: declarative AI queries vs. imperative prompting
7. Call to action: `pip install spl-llm` / `pip install spl-flow`

**Target audience**: Data engineers, ML practitioners, technical product managers —
people who know SQL and are curious about LLMs but frustrated by prompt chaos.

**Why it will resonate**: Everyone has had the experience of getting a confident,
wrong answer from an AI. This article turns that frustration into a systems
engineering insight: the problem is not the model, it is the lack of a query
language.

---

## Files in This Use Case

| File | Description |
|------|-------------|
| `papers-by-top-prize-winners-recently_v1.spl` | The SPL query (3 PROMPT statements) |
| `use-case-2-top-papers.md` | This document — design notes + blog draft |

---

## Run It

```bash
# Quick test — Claude CLI (free, no API key needed)
spl execute examples/format-cte-join/papers-by-top-prize-winners-recently_v1.spl \
    --adapter claude_cli \
    --param years="2020-2025"

# BENCHMARK — compare three models (requires OpenRouter API key)
spl benchmark examples/format-cte-join/papers-by-top-prize-winners-recently_v1.spl \
    --model anthropic/claude-sonnet-4-5 \
    --model openai/gpt-4o \
    --model google/gemini-pro-1.5 \
    --adapter openrouter \
    --json > prize_papers_comparison.json

# Preview token plan without running (free — no LLM call)
spl explain examples/format-cte-join/papers-by-top-prize-winners-recently_v1.spl
```

---

*Last updated: February 2026 — SPL v0.1.0*
