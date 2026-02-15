# SPL Paper — Test & Benchmark Scripts

All scripts that generate results, tables, and figures referenced in the paper.
Run each from the **repo root** (`/home/papagame/projects/digital-duck/SPL`).

---

## Quick-start: run everything

```bash
# 1. Unit tests (40 tests total)
pytest tests/ -v

# 2. All benchmark experiments (Experiments 1-5)
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification

# 3. Regenerate all PDF figures
python -m tests.benchmarks.generate_figures
```

---

## Benchmark Scripts (`tests/benchmarks/`)

### `bench_developer_experience.py` — **Experiment 1** (Section 7.1)

**Produces:** Table 4 (Developer Experience) · data for Figure 1 (LoC bar chart)

Compares lines-of-code across 5 benchmark tasks: Simple QA, RAG-augmented QA,
Multi-step CTE, Function Reuse, and Cached Repeat. Measures SPL vs. equivalent
imperative Python (from `imperative_baselines.py`) and counts manual token-counting
operations eliminated.

```bash
python -m tests.benchmarks.bench_developer_experience
```

Key result: **65% average LoC reduction**, 35 manual token-counting operations eliminated.

---

### `bench_token_optimization.py` — **Experiment 2** (Section 7.2)

**Produces:** Table 5 (Token Allocation) · data for Figure 2 (stacked allocation) · Figure 3 (compression)

Runs the same query structure at budgets from 2K to 32K tokens, measuring how the
optimizer allocates tokens across system role, question, RAG docs, memory, output, and
buffer. Also sweeps the context-to-budget ratio from 0.5× to 4× to show proportional
compression behaviour.

```bash
python -m tests.benchmarks.bench_token_optimization
```

---

### `bench_cost_estimation.py` — **Experiment 3** (Section 7.3)

**Produces:** Table 6 (Cross-Model Cost Estimation) · data for Figure 4 (cost bar chart)

Runs `EXPLAIN` on the same 8K-budget query with six different `USING MODEL` values
(GPT-4 legacy, Claude Opus 4.6, Claude Sonnet 4.5, GPT-4o, GPT-3.5 Turbo, Claude
Haiku 4.5) and records pre-execution cost estimates. No LLM API calls are made.

```bash
python -m tests.benchmarks.bench_cost_estimation
```

Key result: **68× cost spread** visible before any tokens are spent.

---

### `bench_explain_showcase.py` — **Experiment 4** (Section 7.4)

**Produces:** EXPLAIN verbatim output (reproduced in Section 7.4)

Runs the full parse → analyze → optimize → explain pipeline on four example `.spl`
files (`hello_world.spl`, `rag_query.spl`, `multi_step.spl`, `custom_function.spl`)
and captures the formatted execution plan output for paper inclusion.

```bash
python -m tests.benchmarks.bench_explain_showcase
```

---

### `bench_feature_verification.py` — **Experiment 5** (Section 7.5)

**Produces:** 20-item feature verification checklist (Section 7.5)

Systematically tests every competitive claim made in Table 3 (Feature Comparison):
declarative syntax, token budgeting, EXPLAIN, RAG, memory, CTEs, UDFs, provider
adapters, compression, and zero-dependency parser. All 20 checks must pass.

```bash
python -m tests.benchmarks.bench_feature_verification
```

Expected output: `20/20 checks PASSED`.

---

### `generate_figures.py` — **Figure generation**

**Produces:** `docs/paper/figures/figure{1,2,3,4}_*.pdf`

Reads JSON results written by the benchmark scripts from `docs/paper/data/` and
renders all four paper figures as publication-ready PDFs using matplotlib.

**Prerequisites:** run the four benchmark experiments first (they write to `data/`).
Requires `matplotlib` (`pip install matplotlib`).

```bash
python -m tests.benchmarks.generate_figures
```

---

### `imperative_baselines.py` — Baseline code (Experiment 1 reference)

Not executed directly. Defines `BASELINES` dict containing the imperative Python
implementations of the same 5 benchmark tasks used in Experiment 1 for LoC counting.
Imported by `bench_developer_experience.py`.

---

### `bench_utils.py` — Shared utilities

Not executed directly. Provides `parse_and_optimize()`, `read_example()`,
`format_table()`, `save_results()`, `DATA_DIR`, `FIGURES_DIR`, `EXAMPLES_DIR`
constants used by all benchmark scripts.

---

## Unit Test Scripts (`tests/`)

### `test_lexer.py` — **Lexer** (14 tests, Section 7.6)

Covers: keyword tokenization (case-insensitive), string literals (single/double quote),
integer and float literals, dot-notation (`context.field`), `$$` delimiters,
`--` comments, operator tokens, and error cases.

```bash
pytest tests/test_lexer.py -v
```

---

### `test_parser.py` — **Parser** (20 tests, Section 7.6)

Covers: basic `PROMPT` statements, `GENERATE` clauses, `WHERE` conditions, CTEs
(`WITH ... AS`), `STORE RESULT IN`, `EXPLAIN`, `EXECUTE`, and end-to-end parsing
of all four example `.spl` files.

```bash
pytest tests/test_parser.py -v
```

---

### `test_optimizer.py` — **Optimizer** (6 tests, Section 7.6)

Covers: execution plan generation, token allocation arithmetic, execution ordering
(memory > cache > RAG > context), `EXPLAIN` output rendering, and over-budget
proportional compression.

```bash
pytest tests/test_optimizer.py -v
```

---

### `test_storage.py` — **Storage backends**

Covers: FAISS and ChromaDB vector store interface parity (parametrized test suite),
SQLite memory store operations, and cache TTL behaviour.

```bash
pytest tests/test_storage.py -v
```

---

## Example SPL files (`examples/`)

The benchmark scripts read from these files:

| File | Used by |
|------|---------|
| `hello_world.spl` | Exp 1 (Simple QA, Cached Repeat), Exp 4 |
| `rag_query.spl` | Exp 1 (RAG-augmented QA), Exp 4 |
| `multi_step.spl` | Exp 1 (Multi-step CTE), Exp 4 |
| `custom_function.spl` | Exp 1 (Function Reuse), Exp 4 |

---

## Output locations

| Artifact | Location |
|----------|----------|
| Benchmark JSON results | `docs/paper/data/*.json` |
| PDF figures | `docs/paper/figures/figure{1,2,3,4}_*.pdf` |
| Unit test results | stdout / pytest report |
