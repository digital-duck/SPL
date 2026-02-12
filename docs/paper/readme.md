# SPL arxiv Paper - TODO List

## Status: Draft Complete (Feb 12, 2026)

Paper: `spl-paper.tex` | Bib: `references.bib` | Figures: `figures/` | Data: `data/`

---

## Before Submission

### Paper Content
- [ ] Proofread entire paper for clarity, grammar, and flow
- [ ] Verify all table/figure numbers match cross-references
- [ ] Check that EBNF grammar in paper matches `docs/grammar.ebnf`
- [ ] Review Abstract - ensure it stands alone (many readers only read this)
- [ ] Ensure "generative knowledge base" framing is prominent in intro
- [ ] Add page numbers and line numbers (arxiv formatting)

### Competitive Analysis (Section 7: Related Work)
- [ ] Verify Prompty latest features (check https://prompty.ai and GitHub)
- [ ] Verify DSPy latest version and features (check https://github.com/stanfordnlp/dspy)
- [ ] Check if LMQL is still active or archived
- [ ] Search arxiv for any new prompt language papers (2025-2026)
- [ ] Add POML (Prompt Optimization Markup Language) by Microsoft if published
- [ ] Check for any LangChain declarative features added recently

### Figures
- [ ] Review all 4 figures for readability (font sizes, labels, legend)
- [ ] Consider adding architecture diagram as a proper figure
- [ ] Ensure all figures are vector PDF (not rasterized)

### References
- [ ] Verify all BibTeX entries have correct year, venue, and authors
- [ ] Add any missing citations (SQL standard history, ANSI SQL)
- [ ] Consider citing recent Prompt Engineering survey papers

### Optional Enhancements
- [ ] Add "Threats to Validity" subsection in Evaluation
- [ ] Add benchmark with actual LLM execution (requires API keys + cost)
- [ ] Add user study or developer survey results (if time permits)
- [ ] Add "Reproducibility" statement with GitHub link
- [ ] Consider adding Appendix with full EBNF grammar

---

## After Submission

### Package Publishing
- [ ] Register `spl-lang` on PyPI (test with TestPyPI first)
- [ ] Add GitHub Actions CI (run tests on push)
- [ ] Add badges to README (PyPI version, tests passing, license)
- [ ] Create GitHub release v0.1.0

### Documentation
- [ ] Write tutorial: "SPL in 5 Minutes for SQL Developers"
- [ ] Add more examples (multi-model comparison, conversation chain, code review)
- [ ] Create VS Code syntax highlighting extension for `.spl` files
- [ ] Complete `docs/dev/co-creation-log.md` with full session details

### Community & Outreach
- [ ] Post on Hacker News
- [ ] Post on r/MachineLearning and r/LanguageTechnology
- [ ] Share on Twitter/X with SQL community hashtags
- [ ] Submit to newsletters (The Batch, TLDR AI, etc.)
- [ ] Reach out to SQL-focused YouTubers/bloggers
- [ ] Present at local meetups or conferences

### SPL v0.2 Roadmap
- [ ] Streaming generation support
- [ ] Multi-turn conversation (PROMPT chains)
- [ ] Materialized prompts (pre-computed prompt fragments)
- [ ] Transaction semantics (multi-step with rollback)
- [ ] Real embedding model for RAG (replace hash-based prototype)
- [ ] EXPLAIN ANALYZE (actual execution metrics, not just estimates)
- [ ] Interactive REPL (`spl shell`)

---

## Quick Commands

```bash
# Run all tests
pytest tests/ -q

# Run all benchmarks
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification

# Regenerate figures
python -m tests.benchmarks.generate_figures

# Compile LaTeX
cd docs/paper && pdflatex spl-paper && bibtex spl-paper && pdflatex spl-paper && pdflatex spl-paper

# Validate examples
spl validate examples/hello_world.spl
spl validate examples/rag_query.spl
spl validate examples/multi_step.spl
spl validate examples/custom_function.spl
```
