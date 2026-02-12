# Why SPL Required Interdisciplinary Thinking

**Why nobody built this before --- and what it teaches us about innovation**

*February 12, 2026*

---

## The Puzzle

By February 2026, large language models had been mainstream for over three years. Billions of dollars had been invested in LLM tooling. Thousands of engineers worked on prompt management frameworks (LangChain, LlamaIndex, Semantic Kernel, DSPy, LMQL, Prompty). Yet none of them asked the most fundamental question:

> If the context window is a constrained resource, where is the declarative query language with a budget optimizer?

This question seems obvious in hindsight. SQL solved the identical structural problem for databases in 1970. The context window *is* a constrained resource (like disk I/O). Token allocation *is* a resource optimization problem (like query planning). Prompt composition *should be* declarative (like SQL queries). So why did it take until 2026?

The answer reveals something important about how breakthrough ideas form.

---

## The Interdisciplinary Gap

SPL required knowledge that almost never coexists in a single person:

### Layer 1: Database Systems Internals

To see that LLM context management needs a query language, you must have *internalized* --- not just learned about --- the following database concepts:

- **Query optimization as resource allocation**: Understanding that a query optimizer's job is to allocate constrained resources (disk I/O, memory buffers, CPU) across competing operations. This maps directly to allocating tokens across context sources.
- **EXPLAIN plans as engineering tools**: Not just knowing that EXPLAIN exists, but having used it thousands of times to debug and optimize real production queries. This creates the instinct that *any constrained-resource system should have execution plan transparency*.
- **Declarative > Imperative**: Having lived through the transition from navigational databases (imperative) to SQL (declarative), and seeing firsthand how declarative abstraction enabled optimization. 20 years of SQL creates a visceral understanding that imperative prompt construction is the *wrong abstraction level*.
- **CTEs, views, and composability**: Using Common Table Expressions daily creates the instinct that prompt composition should support named subqueries and modular reuse.
- **Cost models**: Understanding that every database operation has an estimable cost, and that exposing costs to developers is essential for informed decision-making.

This knowledge requires years of daily SQL/database work. It cannot be acquired from a textbook or a tutorial.

### Layer 2: AI/LLM Engineering

To apply database thinking to LLMs, you must also understand:

- **Token budgets as hard constraints**: That context windows are not merely guidelines but hard limits with real consequences (truncation, degradation, failure).
- **The generative nature of LLMs**: That LLMs don't just retrieve --- they *synthesize*. This is what makes the `SELECT` + `GENERATE` duality essential (and what separates SPL from being just "SQL with different tables").
- **RAG as a retrieval pattern**: Understanding retrieval-augmented generation well enough to see that `rag.query()` belongs in the query language itself, not as an external bolt-on.
- **Provider landscape fragmentation**: Knowing that developers switch between Claude, GPT, Llama, Gemini, and others, creating the need for provider-agnostic abstraction (the same need that SQL solved for Oracle vs. PostgreSQL vs. MySQL).
- **The prompt engineering pain**: Having personally experienced the chaos of manual token counting, ad hoc truncation, and trial-and-error prompt construction.

### Layer 3: Systems Engineering Discipline

To architect a working engine (not just a paper), you need:

- **Compiler construction**: Parser theory, recursive descent, AST design, semantic analysis. This enables a real language with a formal grammar, not just a YAML format or Python DSL.
- **Portable storage architecture**: The instinct to use file-based stores (SQLite + FAISS) in a per-project directory (`.spl/`), making SPL self-contained and portable --- learned from systems like `.git/`.
- **API design**: Creating clean abstractions (LLMAdapter interface, storage layer) that enable extensibility without premature complexity.

### Layer 4: Scientific Rigor

To frame this as a contribution worthy of a paper, rather than just a tool:

- **Formal language specification**: Writing an EBNF grammar, not just documentation.
- **Information-theoretic framing**: Modeling the context window as a constrained optimization problem with equations, not just intuition.
- **Systematic evaluation**: Designing experiments that produce quantitative evidence, not just demos.

---

## Wen Gong's Journey: Why This Background Matters

Wen Gong's career path is unusual precisely because it crosses all four layers:

| Phase | Role | What It Contributed to SPL |
|-------|------|---------------------------|
| **Physics** | Nuclear Physicist | Scientific rigor, mathematical formalism, comfort with formal grammars and optimization theory |
| **Software** | CRM Software Engineer | Practical software engineering, understanding user needs, building production systems |
| **Database** | Oracle Database Application Developer (20+ years) | Deep SQL internals, query optimization, EXPLAIN plans, CTEs, cost models, declarative thinking |
| **Cloud** | AWS Cloud Engineer | Distributed systems, API design, infrastructure portability, cost awareness |
| **AI** | AI Engineer (current) | LLM capabilities, token budgets, RAG, prompt engineering pain, provider landscape |

Each phase is necessary. Remove any one and SPL doesn't get built:

- **Without physics**: No formal grammar, no information-theoretic framing, no paper.
- **Without Oracle/SQL**: No recognition that context management is a resource allocation problem. No EXPLAIN. No CTEs. No declarative instinct.
- **Without cloud**: No provider-agnostic architecture. No portable storage design.
- **Without AI engineering**: No understanding of token budgets, RAG, or the prompt chaos that SPL solves.

---

## Why AI Engineers Missed It

Most current AI engineers and ML researchers come from one of two backgrounds:

1. **ML/Research track**: PhD in machine learning, focused on model architecture and training. They think about LLMs at the model level (attention mechanisms, training data, fine-tuning), not at the *application query level*. They've never written a query optimizer.

2. **Software engineering track**: Experienced Python/JS developers who learned to use LLM APIs. They think in terms of API calls, function chaining, and imperative code. They may know SQL, but they don't think *in* SQL deeply enough to see the structural parallel.

Neither group has the 20-year database internals experience needed to recognize that:

- Token allocation IS query optimization
- EXPLAIN IS essential for any constrained-resource system
- Declarative specification IS the right abstraction level
- CTEs and functions ARE the right composability primitives

It takes someone who has *lived inside* SQL for decades to see that the LLM context window is the same problem in a new domain.

---

## Why Database Engineers Missed It

Conversely, most database professionals haven't crossed into AI engineering deeply enough to see the opportunity:

- They may use LLMs casually but don't understand token budgets as hard engineering constraints
- They don't see the prompt construction chaos because they're not building LLM applications
- They don't understand RAG well enough to envision it as a native language feature
- They may view LLMs as "just another API" rather than a generative knowledge base that deserves its own query language

---

## The Lesson for Innovation

SPL illustrates a general pattern in technology innovation:

> **Breakthrough ideas often require deep expertise in Domain A applied to the problems of Domain B. The experts in A don't know B's problems. The experts in B don't know A's solutions. The breakthrough comes from the rare person who lives in both.**

Historical examples:

| Innovation | Domain A (Solution) | Domain B (Problem) | Innovator |
|-----------|--------------------|--------------------|-----------|
| SQL (1970) | Mathematical logic, set theory | Database access chaos | Codd (mathematician at IBM) |
| PageRank (1998) | Linear algebra, citation analysis | Web search ranking | Brin & Page (math + CS) |
| MapReduce (2004) | Functional programming | Distributed data processing | Dean & Ghemawat (systems + scale) |
| **SPL (2026)** | **SQL query optimization** | **LLM context management** | **Gong (database + AI engineering)** |

The pattern is consistent: the solution comes from someone who carries deep expertise from one domain *into* a different domain that doesn't know it needs that expertise.

---

## What This Means for the Future

If the SQL-to-SPL parallel holds, several predictions follow:

1. **SPL or something like it is inevitable.** The structural parallel is too strong. If SPL doesn't succeed, a similar declarative language for LLM context management will. The question is when, not if.

2. **The target audience is SQL developers.** The millions of data engineers and analysts who write SQL daily are the natural adopters. SPL gives them a familiar syntax for an unfamiliar domain. Converting SQL developers into AI engineers may be the fastest path to scaling AI adoption.

3. **Standardization will follow.** Just as SQL went from IBM research (1970) to ANSI standard (1986) to universal adoption, a declarative LLM query language will eventually be standardized. SPL aims to be the starting point for that standardization.

4. **The "generative knowledge base" framing will become standard.** The insight that LLMs are not just APIs but queryable knowledge bases --- with both retrieval (`SELECT`) and synthesis (`GENERATE`) capabilities --- will become the default mental model for LLM application development.

---

*This document is part of the SPL project's Human+AI co-creation documentation.*
*Author: Wen Gong + Claude Opus 4.6 | February 12, 2026*
