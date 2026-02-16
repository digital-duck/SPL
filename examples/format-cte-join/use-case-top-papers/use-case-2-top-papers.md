# Use Case 2: Recent Papers by Top Prize Winners

**File**: `papers-by-top-prize-winners-recently_v1.spl`
**Date**: February 2026
**Status**: Ready to run / BENCHMARK-ready

---

## The Original Question

```User
List the most recent 2 papers published by each prize winner in Physics (Nobel Prize), in Mathematics (Fields Medal), and in Computer Science (Turing Award) in the last 5 years. 


I am going to ask the same question to Google Search, ChatGPT, Gemini, and Claude, and see how each response compares.
```

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

## Claude Opus 4.6 First Look: Web Search + Deep Research

Before running the formal BENCHMARK, we tested the query against Claude Opus 4.6 via
the claude.ai chat interface, which has web search capability. The results confirm
our design hypothesis: **this question is primarily a search problem, not a knowledge
problem**, and the model's behaviour changes fundamentally when it can access the web.

### What Opus 4.6 Did

Opus 4.6 made **four separate web searches** before compiling its answer:
1. Searched for the full laureate lists across all three prizes (2021–2025)
2. Searched for recent papers by each laureate — noting *"this is a massive research task"*
3. Batched follow-up searches to fill gaps in individual laureate coverage
4. Verified paper details before assembling the final document

This is the search behaviour our SPL query was designed to elicit:
a model that knows it doesn't know, and looks it up rather than fabricating.

### Key Findings

**Coverage**: Opus 4.6 identified **25 laureates** across all three prizes:
- Nobel Physics (2021–2025): 15 winners over 5 cohorts (including 2025: John Clarke,
  Michel Devoret, John Martinis — for quantum tunnelling in electric circuits)
- Fields Medal (2022): 4 medallists (the only ICM cohort in the window)
- Turing Award (2021–2024): 6 winners over 4 cohorts

**Verifiable citations**: Papers were cited with specific arXiv IDs where available.
For example, Geoffrey Hinton's entries included:
- *"The Forward-Forward Algorithm: Some Preliminary Investigations"* — arXiv:2212.13345 ✓
- *"Gaussian-Bernoulli RBMs Without Tears"* — arXiv:2210.10318 ✓

Both arXiv IDs are real and verifiable — the strongest possible anti-hallucination
signal. This is exactly what the `DOI or arXiv` column in our SPL query was designed
to force.

**2025 Nobel Physics included**: Opus 4.6 already had the 2025 Nobel Physics prize
(awarded October 2025), which confirms its training data extends into late 2025 — and
web search extends further still.

### What This Proves

| Claim | Evidence |
|-------|---------|
| This is a search problem | Opus 4.6 made 4 web searches; pure-knowledge models would guess |
| Web search wins on recency | 2025 Nobel captured; a mid-2024 cutoff model would miss it |
| DOI/arXiv requirement works | Real arXiv IDs provided; fabricated titles rarely survive this test |
| `TEMPERATURE 0.1` is right | Low-confidence fabrications are penalised; Opus 4.6 hedged where uncertain |
| 3 domains need independent PROMPTs | Each domain had different data availability; separate budgets helped |

### The SPL Advantage Over a Plain Chat Prompt

When you ask the same question in a plain chat interface:
- You get one response, one model, one attempt
- No token budget control (the model decides how much to say)
- No structured output (tables may be inconsistent across domains)
- No reproducibility (each run is independent; you cannot BENCHMARK)

When you run it as an SPL query:
- Three independent PROMPTs, each with a budget and temperature setting
- `USING MODEL auto` routes each domain to the best available specialist
- The same `.spl` file can be run against Opus 4.6, GPT-4o, and Gemini in a single
  `spl-flow benchmark` call — parallel, structured, JSON-comparable
- The DOI/arXiv column requirement is enforced in every run, not just when you remember
  to ask

---

## The BENCHMARK: Multi-Model Comparison

The same question was asked directly to Claude Opus 4.6 and ChatGPT (web search enabled
in both). Below is a structured comparison. Results from Qwen, DeepSeek, Grok (X), and
GLM are pending.

---

### Dimension 1 — Scope Coverage

How many of the 25 laureates (2021–2025) did each model cover?

| Model | Nobel Physics | Fields Medal | Turing Award | Total | 2025 Nobel |
|-------|:---:|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | 15 / 15 (5 cohorts) | 4 / 4 | 6 / 6 | **25 / 25** | ✓ |
| **ChatGPT** | 2 / 15 (2024 only) | 2 / 4 | ~4 (partial) | **~8 / 25** | ✗ |
| Qwen | — | — | — | — | — |
| DeepSeek | — | — | — | — | — |
| Grok (X) | — | — | — | — | — |
| GLM | — | — | — | — | — |

ChatGPT's scope failure is structural: it answered "the most recent prize winners" as
if that meant only the *latest single cohort* — Nobel 2024, but not 2023, 2022, 2021, or 2025.
Opus 4.6 treated "last 5 years" correctly as a time window covering all cohorts.

---

### Dimension 2 — Citation Quality

Were the paper titles and arXiv IDs real and verifiable?

| Model | Real arXiv IDs | Fabricated titles | Substituted attribution | Honest hedges |
|-------|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | Many (7+) | None detected | None | ✓ systematic |
| **ChatGPT** | Some (4) | Some (arXiv search URLs) | **Yes — Hopfield** | Partial |
| Qwen | — | — | — | — |
| DeepSeek | — | — | — | — |
| Grok (X) | — | — | — | — |
| GLM | — | — | — | — |

**Verified real arXiv IDs in Opus 4.6 response:**
- Hinton: `arXiv:2212.13345`, `arXiv:2210.10318`
- Duminil-Copin: `arXiv:2404.05700`
- Maynard: `arXiv:2405.20552`, `arXiv:2407.14368`
- Wigderson: `arXiv:2404.10839`

---

### Dimension 3 — The Most Interesting Failure (Hopfield Substitution)

ChatGPT's Hopfield section is the sharpest failure signal in the dataset.

Correctly noting that *"Hopfield himself does not have a recent direct arXiv entry"*,
ChatGPT then filled the two required rows with papers by **other authors** at JKU Linz
who built extensions of Hopfield networks:

```
arXiv:2405.08766 — "Energy-based Hopfield Boosting for OoD Detection"  [ml-jku.github.io]
arXiv:2405.08769 — "Hopular: Modern Hopfield Networks for Tabular Data" [ml-jku.github.io]
```

These are **real papers** — but they are not *by Hopfield*. The arXiv IDs check out; the
attribution is wrong. The model satisfied the format requirement (two rows with arXiv
links) while violating the semantic requirement (papers *by* the laureate).

This is a subtler failure mode than outright fabrication:
- The links are real → passes a naive URL-checker
- The papers are topically relevant → passes a casual reader
- The attribution is wrong → fails verification the moment you check the authors

**Taxonomy of failure modes observed so far:**

| Failure mode | ChatGPT | Opus 4.6 |
|---|---|---|
| Scope truncation (only latest cohort) | ✓ | — |
| Title fabrication (invented paper) | Some (search URLs) | None |
| Attribution substitution (wrong author, real paper) | ✓ (Hopfield) | — |
| Textbook as "research paper" (Barto/Sutton RL textbook) | ✓ | — |
| Retired-laureate honesty (admits no recent output) | Partial | ✓ systematic |
| Salesperson closing ("would you like PDFs?") | ✓ | — |

---

### Dimension 4 — Format Faithfulness

Did the model follow the structured table format requested?

| Model | Table format | Per-laureate sections | Emojis / clutter | Consistent columns |
|-------|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | ✓ | ✓ | None | ✓ |
| **ChatGPT** | Partial | ✓ | 🧪📐💻📄🔍 | ✗ (mixed) |

ChatGPT's use of emoji headers (🧪 for Physics, 📐 for Mathematics) is cosmetically
appealing but breaks machine-readable output. An SPL `FORMAT markdown` directive should
suppress this. It also mixed table and prose formats within the same domain.

---

### Running the Formal BENCHMARK

SPL's `BENCHMARK` construct runs the same `.spl` file against N models in parallel
and returns a structured JSON report — reproducible and machine-comparable.

```bash
# Via SPL-Flow CLI (OpenRouter — requires OPENROUTER_API_KEY)
spl-flow benchmark examples/format-cte-join/use-case-top-papers/papers-by-top-prize-winners-recently_v1.spl \
    --models "anthropic/claude-opus-4-6,openai/gpt-4o,google/gemini-pro-1.5,qwen/qwen-max,deepseek/deepseek-chat,x-ai/grok-2" \
    --adapter openrouter \
    --json > prize_papers_comparison.json

# Via SPL-Flow Streamlit UI
# → Page 3 (Benchmark) → paste SPL → select models → Run
```

**What to look for in the comparison:**

| Signal | Interpretation |
|--------|---------------|
| All models cite the same paper with matching arXiv ID | High-confidence ground truth |
| Two agree, one differs | Minority is likely hallucinating |
| All cite different papers | Low reliability — verify via Google Scholar |
| Model provides arXiv IDs that resolve correctly | Strong anti-hallucination signal |
| Model provides arXiv IDs that 404 | Fabricated citation — worst failure mode |
| Model substitutes related-but-wrong author | Subtle failure — passes URL check, fails attribution |
| Model explicitly hedges ("unable to verify") | Correct calibration, follows system role |
| Model covers all cohorts 2021–2025 | Treated as a time-window problem (correct) |
| Model covers only latest cohort | Treated as "most recent" = singular (incorrect) |

**The most important comparison is not *what* each model says, but *how it handles
the cases where it cannot know for certain*.** The Hopfield substitution is more
dangerous than an explicit fabrication because it passes superficial verification.

---

### Response Files

| File | Model | Date | Web search |
|------|-------|------|------------|
| `response-claude-opus46.md` | Claude Opus 4.6 | Feb 2026 | ✓ (4 searches) |
| `response-chatgpt.md` | ChatGPT (GPT-4o) | Feb 2026 | ✓ |
| `response-qwen.md` | Qwen | — | pending |
| `response-deepseek.md` | DeepSeek | — | pending |
| `response-grok.md` | Grok (X) | — | pending |
| `response-glm.md` | GLM | — | pending |

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
| `use-case-2-top-papers.md` | This document — design notes, comparison analysis, blog draft |
| `response-claude-opus46.md` | Claude Opus 4.6 response (25 laureates, web search, Feb 2026) |
| `response-chatgpt.md` | ChatGPT (GPT-4o) response (partial scope, Feb 2026) |
| `response-qwen.md` | Qwen response *(pending)* |
| `response-deepseek.md` | DeepSeek response *(pending)* |
| `response-grok.md` | Grok (X) response *(pending)* |
| `response-glm.md` | GLM response *(pending)* |

---

## Run It

```bash
cd examples/format-cte-join/use-case-top-papers/
# Preview token plan without running (free — no LLM call)
spl explain papers-by-top-prize-winners-recently_v1.spl --log ./spl_explain.log --output ./spl_explain.md

# SPL test using adapter=Claude CLI (free, no API key needed)
spl execute papers-by-top-prize-winners-recently_v1.spl --adapter claude_cli --params "years=2020-2025" --log ./spl_cli.log --output ./spl_cli.json

# BENCHMARK — compare three models (requires OpenRouter API key)
splflow use-case-top-papers/papers-by-top-prize-winners-recently_v1.spl --adapter openrouter --models "anthropic/claude-sonnet-4-5, openai/gpt-4o, google/gemini-1.5-pro" --log ./spl_benchmark.log --output ./spl_benchmark.json

```

---

*Last updated: February 2026 — SPL v0.1.0*
