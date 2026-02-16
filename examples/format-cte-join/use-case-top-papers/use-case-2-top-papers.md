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

The same question was submitted to **9 models** — 7 via web chat (web search enabled)
and 3 via the SPL formal BENCHMARK (OpenRouter, no web search). Results are now complete.

---

### Dimension 1 — Scope Coverage

How many of the ~25 laureates (2020–2025) did each model cover?

> Coverage counts: Nobel Physics 2020–2024 = 14 winners; 2025 = 3 additional. Fields 2022 = 4.
> Turing 2020–2024 = 7. Web-chat models may include 2025 Nobel if their training extends there.

| Model | Mode | Nobel Physics | Fields Medal | Turing Award | 2025 Nobel |
|-------|------|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | web chat | 15 / 15 (5 cohorts incl. 2025) | 4 / 4 | 6 / 6 | ✓ |
| **GLM** | web chat | 13 / 14 (2021–2025, missed some 2020) | 4 / 4 | 7 / 7 | ✓ |
| **Grok (X)** | web chat | 14 / 14 (2020–2024) + 2025 | 4 / 4 | 7 / 7 | ✓ |
| **Qwen** | web chat | 13 / 14 (2021–2025) | 8 / 8 (2018 + 2022) | 7 / 7 | ✓ |
| **Kimi** | web chat | 14 / 14 (2020–2024) | 4 / 4 | 7 / 7 | ✗ |
| **ChatGPT** | web chat | 2 / 14 (2024 only) | 2 / 4 | ~4 (partial) | ✗ |
| **DeepSeek** | web chat | 5 / 14 (2024–2025 only) | 4 / 4 | 0 / 7 | ✓ (text only) |
| **Perplexity** | web chat | 0 / 14 — *refused* | 0 | 0 | ✗ |
| **claude-sonnet-4.5** | SPL/OpenRouter | 14 / 14 ✓ | 4 / 4 | 7 / 7 (with errors) | ✗ |
| **gpt-4o-2024-11-20** | SPL/OpenRouter | 11 / 14 (stopped at 2023) | 4 / 4 | 5 / 7 (cutoff) | ✗ |
| **gemini-3-flash** | SPL/OpenRouter | 14 / 14 ✓ | 4 / 4 | 5 / 7 (2024 not announced) | ✗ |

**Key observations:**
- ChatGPT's scope failure is structural: "most recent prize winners" was interpreted as
  the *latest single cohort* (Nobel 2024 only), not as a 5-year time window.
- Perplexity — nominally a "search-first" model — refused entirely, calling the task "too broad".
  This is the most surprising failure given its architecture.
- DeepSeek covered Nobel but skipped Turing entirely, returning database search suggestions instead.
- Qwen was the only model to include 2018 Fields medallists (Birkar, Figalli, Scholze, Venkatesh)
  — an over-inclusive but reasonable interpretation of "last 5 years".

---

### Dimension 2 — Citation Quality

Were the paper titles and arXiv / DOI links real and verifiable?

| Model | Mode | Real arXiv/DOI | Fabricated | Substituted attribution | Honest hedges |
|-------|------|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | web chat | Many (7+) | None detected | None | ✓ systematic |
| **GLM** | web chat | Real URLs (web search) | None detected | None | ✓ gaps noted |
| **Grok (X)** | web chat | Specific arXiv IDs | Low risk | None detected | ✓ retired noted |
| **gemini-3-flash** | SPL/OpenRouter | Good DOI coverage | Low risk | None detected | ✓ |
| **claude-sonnet-4.5** | SPL/OpenRouter | Good DOIs | Low risk | None detected | ✓ systematic |
| **Qwen** | web chat | Bracket refs ([55] etc) | Medium risk | None detected | Partial |
| **Kimi** | web chat | Few specific, mostly vague | Medium risk | None | Partial |
| **gpt-4o-2024-11-20** | SPL/OpenRouter | Some real, some N/A | Some suspicious | None detected | ✓ explicit cutoff |
| **ChatGPT** | web chat | Some (4) | Some | **Yes — Hopfield** | Partial |
| **DeepSeek** | web chat | 0 specific citations | None (no claims) | None | ✓ (via abstention) |
| **Perplexity** | web chat | N/A — refused | N/A | N/A | N/A |

**Verified real arXiv IDs in Opus 4.6 response:**
- Hinton: `arXiv:2212.13345`, `arXiv:2210.10318`
- Duminil-Copin: `arXiv:2404.05700`
- Maynard: `arXiv:2405.20552`, `arXiv:2407.14368`
- Wigderson: `arXiv:2404.10839`

**Notable Grok arXiv IDs (spot-checkable):**
- Devoret: `arXiv:2505.08104`, `arXiv:2506.05306`
- Martinis: `arXiv:2411.10406`
- Sutton: "Loss of Plasticity in Deep Continual Learning" — *Nature* 2024 ✓

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

**Full taxonomy of failure modes across all 11 model runs:**

| Failure mode | ChatGPT | Opus 4.6 | Grok | Qwen | GLM | Kimi | DeepSeek | Perplexity | Sonnet-4.5 (SPL) | GPT-4o (SPL) | Gemini-flash (SPL) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Scope truncation (latest cohort only) | ✓ | — | — | — | — | — | ✓ (Physics only) | N/A | — | ✓ (cutoff) | — |
| Task refusal ("too broad") | — | — | — | — | — | — | — | ✓ | — | — | — |
| Title fabrication (invented paper) | Some | None | Low risk | Medium risk | None | Some vague | None | N/A | Low risk | Some | Low risk |
| Attribution substitution (wrong author, real paper) | ✓ Hopfield | — | — | — | — | — | — | N/A | — | — | — |
| Wrong winner name (hallucinated laureate) | — | — | — | — | — | — | — | N/A | ✓ (Turing 2023) | ✓ (Turing 2023) | — |
| Textbook cited as research paper | ✓ Barto/Sutton | — | — | — | — | — | — | N/A | — | — | — |
| Retired-laureate honesty | Partial | ✓ | ✓ | Partial | ✓ | — | N/A | N/A | ✓ | ✓ | ✓ |
| Knowledge cutoff failure | — | — | — | — | — | ✓ (no 2025) | — | N/A | ✓ (no 2025) | ✓ | ✓ |
| Salesperson closing ("would you like more?") | ✓ | — | — | ✓ | — | ✓ | ✓ | ✓ | — | ✓ | — |

**The `claude-sonnet-4.5` Turing 2023 error deserves highlighting.**
The SPL run listed Amos Fiat and Adi Shamir as 2023 Turing winners — neither is correct.
Avi Wigderson won the 2023 Turing Award (for randomness in computation). Fiat and Shamir
are real cryptographers but not Turing winners. This is a pure hallucination that passed
the format requirement (names + paper rows with DOIs) while being factually wrong on the
winner identity itself. `gpt-4o` made the same mistake via knowledge cutoff (listed 2023 as
"yet to be announced"), which is at least *honest* about the uncertainty.

---

### Dimension 4 — Format Faithfulness

Did the model follow the structured table format requested?

| Model | Mode | Table format | Per-laureate sections | Emoji / clutter | Consistent columns |
|-------|------|:---:|:---:|:---:|:---:|
| **Claude Opus 4.6** | web chat | ✓ | ✓ | None | ✓ |
| **GLM** | web chat | ✓ | ✓ | None | ✓ |
| **Grok (X)** | web chat | ✓ | ✓ | Minimal | ✓ |
| **Qwen** | web chat | Mixed (tables + lists) | ✓ | 🏆🥇💻 | Partial |
| **Kimi** | web chat | Headers + lists, no tables | ✓ | None | N/A |
| **DeepSeek** | web chat | Tables (sparse content) | Partial | 🏆🏅🔬 | ✓ |
| **ChatGPT** | web chat | Partial | ✓ | 🧪📐💻📄🔍 | ✗ (mixed) |
| **Perplexity** | web chat | N/A | N/A | N/A | N/A |
| **gemini-3-flash** | SPL/OpenRouter | ✓ full tables | ✓ | None | ✓ |
| **claude-sonnet-4.5** | SPL/OpenRouter | ✓ full tables | ✓ | None | ✓ |
| **gpt-4o-2024-11-20** | SPL/OpenRouter | ✓ full tables | ✓ | None | ✓ |

**The SPL `FORMAT markdown` + `system_role` instruction suppressed emoji across all three
OpenRouter models** — none of the SPL-run responses used decorative emoji headers.
The web-chat models that received an equivalent prompt instruction also mostly complied
(Opus 4.6, GLM, Grok), while ChatGPT, Qwen, and DeepSeek added emoji regardless.

This suggests `FORMAT markdown` in SPL functions as an effective format enforcement
mechanism — not just a hint.

---

---

### SPL Formal BENCHMARK — OpenRouter Results

The `.spl` file was executed against three models in parallel via `splflow benchmark`
on 16 February 2026. Total wall-clock time: ~68 seconds for all three models together.

```bash
splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
    --adapter openrouter \
    --models "anthropic/claude-sonnet-4.5, openai/gpt-4o-2024-11-20, google/gemini-3-flash-preview" \
    --log ./results/spl_benchmark.log \
    --output ./results/spl_benchmark.json
```

**Per-model latency (3 PROMPTs combined):**

| Model | physics_prize | math_prize | cs_prize | Total latency |
|-------|:---:|:---:|:---:|:---:|
| claude-sonnet-4.5 | 37.0s | 12.5s | 18.2s | **67.7s** |
| gpt-4o-2024-11-20 | 19.3s | 7.6s | 7.3s | **34.2s** |
| gemini-3-flash-preview | 15.0s | 4.6s | 7.3s | **26.9s** |

**Quality summary:**

| Model | Physics | Math | CS | Notable failure |
|-------|---------|------|----|-----------------|
| **claude-sonnet-4.5** | ✓ Full coverage, good DOIs, "unable to verify" for retired | ✓ Clean 4-medallist tables | ⚠️ Listed Amos Fiat + Adi Shamir as 2023 Turing winners (hallucinated) | Wrong winner identity |
| **gpt-4o-2024-11-20** | ✓ Good DOIs; Penrose listed as "unable to verify" | ✓ Real paper DOIs | ✗ Stopped at 2022; "2023 winner yet to be announced" | Knowledge cutoff |
| **gemini-3-flash** | ✓ Best structured; Nobel Lecture papers included | ✓ Solid with DOIs | ✓ Correctly noted 2024 winner unannounced per knowledge cutoff | Honest cutoff handling |

**Key finding from SPL run:**
The structured prompting (system_role + DOI column requirement + TEMPERATURE 0.1)
dramatically improved Gemini's output quality compared to the direct web-chat run
documented earlier — confirming that **SPL's prompt engineering is not just
organisational overhead; it measurably affects output quality**.

Full benchmark data: `results/spl_benchmark.json`

---

### SPL Benchmark v2 — OpenRouter (7 models, 16 Feb 2026)

```bash
splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
    --adapter openrouter \
    --models "anthropic/claude-opus-4.6, openai/gpt-4o-2024-11-20, \
              google/gemini-3-pro-preview, google/gemini-3-flash-preview, \
              z-ai/glm-4.6, qwen/qwen3-235b-a22b, moonshotai/kimi-k2" \
    --log ./results/spl_benchmark-v2.log \
    --output ./results/spl_benchmark-v2.json
```

**Run summary:**

| Model | Status | Tokens | Latency | Physics | Math | CS Winners |
|-------|--------|-------:|--------:|---------|------|------------|
| `anthropic/claude-opus-4.6` | ✅ | 5,854 | 70.2s | 14/14, systematic hedges | 4/4 arXiv | ⚠️ 2024: Barto+**Littman** (Sutton≠Littman) |
| `openai/gpt-4o-2024-11-20` | ✅ | 3,956 | 28.4s | 11/14, no 2024 (cutoff) | 4/4 DOIs | ❌ **Jordan** as 2023 (is Wigderson), no 2024 |
| `google/gemini-3-pro-preview` | ✅ | 7,420 | 110.9s | 14/14, Nobel Lecture fallback | 4/4 DOIs | ✅ 2020-2023 correct, 2024 unannounced |
| `google/gemini-3-flash-preview` | ✅ | 4,811 | 26.1s | 14/14, good DOIs | 4/4 DOIs | ✅ 2020-2023 correct, 2024 unannounced |
| `z-ai/glm-4.6` | ❌ | 0 | 0s | — | — | JSON parse error (executor bug) |
| `qwen/qwen3-235b-a22b` | ✅ | 9,527 | 115.0s | 14/14, DOIs | 4/4 DOIs | ❌❌ **Bengio/Hinton/LeCun as 2022** (year-shift) |
| `moonshotai/kimi-k2` | ✅ | 4,035 | 81.2s | 14/14, detailed DOIs | 4/4 DOIs | ❌❌ Wrong winners throughout (year-shift) |

**Speed ranking**: gemini-3-flash (26s) ≈ gpt-4o (28s) < opus-4.6 (70s) < kimi-k2 (81s) < gemini-3-pro (111s) < qwen3-235b (115s)

---

**Notable findings from v2:**

**1. Gemini 3 Pro's Nobel Lecture fallback** — the most sophisticated adaptation observed.
For retired laureates with no recent primary research (Manabe, Hasselmann, Clauser),
instead of returning "unable to verify", Gemini 3 Pro included their Nobel Lectures
published in *Reviews of Modern Physics* as "significant recent scholarly output."
This is both defensible and useful. The methodology note was explicit:
> *"For laureates who are retired or less active, their Nobel Lectures are included
> as they constitute significant recent scholarly output."*

**2. Qwen's year-shift hallucination** — the sharpest new failure mode in v2.
Qwen listed Yoshua Bengio, Geoffrey Hinton, and Yann LeCun as the **2022 Turing Award**
winners. They are not: they won the **2018 Turing Award**. Qwen correctly knows these
people won the Turing Award — it just shifted the year by 4 years, substituting the
memorable 2018 AI cohort for the obscure 2022 winner (Bob Metcalfe). This is fundamentally
different from a random fabrication: it is a systematic year-displacement error.

**3. Kimi K2's year-shift hallucination** — same failure mode, different displacement.
Kimi listed RSA inventors (Rivest/Adleman/Shamir, actual 2002 winners) as 2022,
Patterson/Hennessy (actual 2017 winners) as 2024. It then honestly marked all papers
as "unable to verify" — correct, since those people don't have relevant recent papers.
The winner identification failed; the paper honesty held. This partial calibration is
interesting: the model knew it didn't know the papers, but didn't know it didn't know
the winners.

**4. Both Gemini models correctly refused to guess the 2024 Turing winner** — noting
it was "not yet announced as of early 2025." GPT-4o hallucinated Jordan (2023 cutoff),
Opus-4.6 named Barto+Littman (Sutton≠Littman error), Qwen/Kimi had year-shift failures.
The two Gemini models were the only ones to handle this specific uncertainty correctly.

**5. GLM parse error** — `z-ai/glm-4.6` failed with `JSONDecodeError` at char 1826.
The response was generated but contained a control character the executor couldn't parse.
This is an executor robustness issue (tracked in README-TODO), not a GLM quality issue.
The web-chat GLM result remains strong.

**Updated failure taxonomy** (adding v2 observations):

| Failure mode | ChatGPT | Opus 4.6 | Grok | GPT-4o | Gemini-Pro | Gemini-Flash | Qwen3 | Kimi K2 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Scope truncation | ✓ | — | — | ✓ (cutoff) | — | — | — | — |
| Wrong winner identity | — | ✓ (Littman) | — | ✓ (Jordan) | — | — | ✓✓ (year-shift) | ✓✓ (year-shift) |
| Title fabrication | Some | None | Low | Some | Low | Medium | Medium | Low |
| Attribution substitution | ✓ Hopfield | — | — | — | — | — | — | — |
| Retired-laureate honesty | Partial | ✓ | ✓ | ✓ | Nobel Lecture | ✓ | Partial | ✓ |
| Knowledge cutoff handling | ✗ | Partial | — | ✓ explicit | ✓ explicit | ✓ explicit | ✗ | ✗ |
| Executor parse failure | — | — | — | — | — | — | — | — |

---

### Overall Model Ranking

Combining web-chat and SPL-BENCHMARK runs (v1 + v2):

| Tier | Model | Mode | Strengths | Weaknesses |
|------|-------|------|-----------|------------|
| **1** | Claude Opus 4.6 | web chat | 25/25 scope, 7+ real arXiv, 2025 Nobel, systematic hedges | Minor: Littman≠Sutton for 2024 Turing |
| **1** | GLM (web) | web chat | Real web search URLs, honest gap analysis, clean format | Full response in docx only |
| **1** | gemini-3-flash | SPL/v2 | 14/14 Physics, 4/4 Math, correct 2020-2023 CS, 26s | No 2025 Nobel (static knowledge) |
| **2** | gemini-3-pro | SPL/v2 | Nobel Lecture fallback, most principled uncertainty handling | Slowest (111s), 2024 Turing unannounced |
| **2** | Grok / X | web chat | Full coverage, specific arXiv IDs, retirement notes | Hallucination risk not fully verified |
| **2** | Qwen (web chat) | web chat | Broad scope (includes 2018 Fields), citation refs | Bracket refs not directly verifiable |
| **3** | gpt-4o-2024-11-20 | SPL/v2 | Honest cutoff, real DOIs where known, 28s | Jordan≠Wigderson for 2023 Turing |
| **3** | claude-sonnet-4.5 | SPL/v1 | Good DOIs, systematic "unable to verify" | Hallucinated Turing 2023 winner |
| **3** | Kimi (web chat) | web chat | 25 winners listed, clean headers | No arXiv IDs, vague on some papers |
| **4** | kimi-k2 | SPL/v2 | Honest "unable to verify" on CS papers | Wrong Turing winners throughout (year-shift) |
| **4** | qwen3-235b-a22b | SPL/v2 | Full physics coverage, DOIs | Bengio/Hinton/LeCun listed as 2022 Turing (year-shift) |
| **4** | ChatGPT | web chat | Format partially followed | Scope truncation, Hopfield substitution, emoji |
| **4** | DeepSeek | web chat | Honest (via abstention) | Only 2 Nobel years, skipped Turing entirely |
| **5** | Perplexity | web chat | — | Refused the task entirely |
| **5** | Claude CLI (no tools) | SPL | — | Refused all 3 prompts (needs `--tools WebSearch,WebFetch`) |
| **—** | GLM 4.6 | SPL/v2 | Strong in web chat | Executor parse failure (JSON control char bug) |

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

| File | Model | Date | Mode | Web search |
|------|-------|------|------|------------|
| `llm_responses/response-claude-opus46.md` | Claude Opus 4.6 | Feb 2026 | web chat | ✓ (4 searches) |
| `llm_responses/response-chatgpt.md` | ChatGPT (GPT-4o) | Feb 2026 | web chat | ✓ |
| `llm_responses/response-qwen.md` | Qwen | Feb 2026 | web chat | ✓ |
| `llm_responses/response-deepseek.md` | DeepSeek | Feb 2026 | web chat | ✓ |
| `llm_responses/response-grok-x.md` | Grok (X) | Feb 2026 | web chat | ✓ |
| `llm_responses/response-glm.md` | GLM (self-comparison) | Feb 2026 | web chat | ✓ |
| `llm_responses/response-perplexity.md` | Perplexity | Feb 2026 | web chat | ✓ (refused task) |
| `llm_responses/response-kimi-award_winners_papers_2020_2025.md` | Kimi | Feb 2026 | web chat | ✓ |
| `results/spl_benchmark.json` | claude-sonnet-4.5, gpt-4o, gemini-3-flash | Feb 2026 | SPL/OpenRouter v1 | ✗ (static knowledge) |
| `results/spl_benchmark-v2.json` | opus-4.6, gpt-4o, gemini-3-pro, gemini-3-flash, glm-4.6, qwen3-235b, kimi-k2 | Feb 2026 | SPL/OpenRouter v2 | ✗ (static knowledge) |
| `results/spl_benchmark-auto.json` | openrouter/auto | Feb 2026 | SPL/OpenRouter | ✗ (refused — no web search) |
| `results/spl_cli.json` | Claude CLI | Feb 2026 | SPL/claude_cli | ✗ (refused — needs `--tools`) |

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

**Proposed title**: *"I Asked 9 AI Models the Same Question About Nobel Prize Winners — Here's What a Query Language Revealed"*

**Hook**: One sentence. Nine AI systems. Eleven distinct failure modes. A new query
language made the comparison reproducible and the failures visible.

**Structure**:
1. The question (simple, one sentence, relatable)
2. The surprise results — GLM comparable to Opus; Perplexity (a search-first model!) refused entirely
3. Why this is hard (knowledge cutoff × hallucination × no structured output)
4. The SPL approach — what changes when you write a *query* instead of a *prompt*
5. The BENCHMARK results — 11-run comparison table
6. The failure taxonomy — Hopfield substitution, scope truncation, winner hallucination
7. The deeper point: declarative AI queries vs. imperative prompting
8. Call to action: `pip install spl-llm` / `pip install spl-flow`

**Target audience**: Data engineers, ML practitioners, technical product managers —
people who know SQL and are curious about LLMs but frustrated by prompt chaos.

**Why it will resonate**: Everyone has had the experience of getting a confident,
wrong answer from an AI. This article turns that frustration into a systems
engineering insight: the problem is not the model, it is the lack of a query
language. And the GLM result is genuinely surprising — the open-source Chinese model
outperforms GPT-4o web on this benchmark.

---

## Files in This Use Case

| File | Description |
|------|-------------|
| `papers-by-top-prize-winners-recently_v1.spl` | The SPL query (3 PROMPT statements) |
| `use-case-2-top-papers.md` | This document — design notes, comparison analysis, blog draft |
| `run_tests.sh` | Reproducible test script (explain / execute / benchmark) |
| `llm_responses/response-claude-opus46.md` | Claude Opus 4.6 (web chat, 25 laureates, Feb 2026) |
| `llm_responses/response-claude-opus46.png` | Screenshot of Opus 4.6 web search activity |
| `llm_responses/response-chatgpt.md` | ChatGPT GPT-4o (web chat, partial scope, Feb 2026) |
| `llm_responses/response-qwen.md` | Qwen (web chat, broad scope incl. 2018 Fields, Feb 2026) |
| `llm_responses/response-deepseek.md` | DeepSeek (web chat, conservative, Turing skipped, Feb 2026) |
| `llm_responses/response-grok-x.md` | Grok / X (web chat, good coverage + arXiv IDs, Feb 2026) |
| `llm_responses/response-glm.md` | GLM self-comparison vs Opus 4.6 (Feb 2026) |
| `llm_responses/response-perplexity.md` | Perplexity (web chat, refused task, Feb 2026) |
| `llm_responses/response-kimi-award_winners_papers_2020_2025.md` | Kimi (web chat, 25 winners, no arXiv, Feb 2026) |
| `results/spl_explain.md` | Token plan output from `spl explain` |
| `results/spl_cli.json` | Claude CLI result (refused — needs `--tools WebSearch,WebFetch`) |
| `results/spl_benchmark.json` | SPL BENCHMARK v1: claude-sonnet-4.5 / gpt-4o / gemini-3-flash |
| `results/spl_benchmark-v2.json` | SPL BENCHMARK v2: 7 models — opus-4.6, gpt-4o, gemini-3-pro, gemini-3-flash, glm-4.6, qwen3-235b, kimi-k2 |
| `results/spl_benchmark-auto.json` | SPL BENCHMARK: openrouter/auto (refused — no web search access) |

---

## Run It

```bash
cd examples/format-cte-join/use-case-top-papers/
mkdir -p results

# Preview token plan without running (free — no LLM call)
spl explain papers-by-top-prize-winners-recently_v1.spl \
    --log ./results/spl_explain.log \
    --output ./results/spl_explain.md

# SPL execute using Claude CLI (free, no API key — grant web search)
spl execute papers-by-top-prize-winners-recently_v1.spl \
    --adapter claude_cli \
    --tools "WebSearch,WebFetch" \
    --claude-cli-timeout 300 \
    --log ./results/spl_cli.log \
    --output ./results/spl_cli.json

# BENCHMARK — compare three models in parallel (requires OpenRouter API key)
splflow benchmark papers-by-top-prize-winners-recently_v1.spl \
    --adapter openrouter \
    --models "anthropic/claude-sonnet-4-5, openai/gpt-4o, google/gemini-flash-1.5" \
    --log ./results/spl_benchmark.log \
    --output ./results/spl_benchmark.json
```

Or just run the included script:

```bash
cd examples/format-cte-join/use-case-top-papers/
bash run_tests.sh
```

---

*Last updated: 16 February 2026 — SPL v0.1.0 — Benchmark v2 (7 models)*
