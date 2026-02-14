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

---

## The human×AI Discovery Process

### Why "×" Is the Right Operator

Three ways to describe the relationship between human and AI in research:

- `human - AI` — subtraction, adversarial. Wrong.
- `human + AI` — addition, two separate contributions that sum. Incomplete.
- `human × AI` — multiplication, each factor amplifies the other. Correct.

The multiplicative framing is precise, not metaphorical. If human insight = 0, the product = 0: AI without direction produces noise. If AI capability = 0, the product = 0: the human is bounded by their own bandwidth. Improving either factor *multiplies* total output. This captures something the additive model misses: the combination is qualitatively different from either factor alone, not just quantitatively larger.

But there is a deeper reason why `×` is the right operator. Discovery is not a deterministic process — it is a **combinatorial, trial-and-error search across a vast space of possibilities**. The `×` operator captures the exploratory, iterative nature of that search.

### Edison's Filament: The Combinatorial Search Principle

Thomas Edison's search for the perfect light bulb filament is a foundational example. He did not derive the answer analytically. He tested thousands of materials — carbonized bamboo, platinum, cotton thread, tungsten — systematically narrowing the search space through experiment. The "invention" was an exhaustive exploration of a combinatorial space, guided by human intuition about which regions were more promising.

The `×` in `human×Edison's-experiments` works because:
- Edison provided the *direction* of the search (energy, constraints, evaluation criteria)
- The experiments provided *coverage* of the solution space
- Neither alone produces the incandescent bulb — you need both the judgment and the search

This is precisely the structure of `human×AI` in discovery: the human provides intuition, domain expertise, and problem framing; the AI provides coverage of the combinatorial space — implementation paths, proof steps, parameter sweeps — that no individual could traverse alone.

### Drug Discovery: Three Eras of Search

Drug discovery illustrates how the *scale* of combinatorial search has evolved across eras:

| Era | Search Medium | Space Explored |
|-----|--------------|---------------|
| **Lab bench** (pre-1980s) | Physical synthesis and biological assay | ~10³ compounds per campaign |
| **Simulation** (1990s–2010s) | Molecular dynamics, docking simulations | ~10⁶ compounds in silico |
| **AI lab** (2020s–present) | Generative models + virtual screening | ~10⁹–10¹² candidate structures |

In each era, the human role shifted — from hands-on chemist, to computational biologist, to ML-guided researcher — but the *role of human judgment* in guiding the search did not diminish. It was amplified. More of the combinatorial work was handled by the tool; more of the strategic work returned to the human. Each transition is `human × (new tool)`, not `human + (new tool)`.

The AI lab is not the end of this sequence. It is the latest expansion of the search space that human judgment can navigate.

### The SPL Genesis: A concrete example

SPL was not designed top-down. It emerged from a `human×AI` search in real time:

- **Thursday morning, meditation**: The insight surfaced — "the LLM context window is a constrained resource, just like disk I/O was for databases. Where is the declarative query language?" This connection required 20+ years of Oracle/SQL experience and current LLM engineering work coexisting in one mind. No AI would have generated this framing unprompted.

- **Thursday morning, first prompt**: The insight was articulated to Claude. It "clicked" immediately — because the structural parallel (token budget = query optimization, SELECT+GENERATE = retrieval+synthesis) is precise and implementable. Within one hour, with a few rounds of feedback, a working prototype existed: lexer, parser, optimizer, executor, CLI.

- **Thursday evening**: The arxiv paper draft was complete.

From meditation to paper draft in one day. Neither alone: the human had the insight but not the implementation time. The AI had the implementation capability but not the insight. The connection was established by the product of both.

### The Provenance Principle

In the vast space of human problems and solutions, a dot can be placed by a human or by an AI. What matters is that the dots are connected and the path is established. The universe does not care about provenance — a theorem is true or false regardless of who found the proof; a useful abstraction works or doesn't regardless of who articulated it.

This is not a new principle. Darwin and Wallace arrived at natural selection independently. The calculus priority dispute between Newton and Leibniz looks petty in retrospect — what survived is the idea. Many of the most important connections in science were made simultaneously by multiple people when the conditions were right.

What is new is the *speed* at which `human×AI` can traverse the problem-solution space. The Edison search that took years can now happen in days. The drug discovery campaign that took a decade can now be explored in silico in months. SPL went from idea to working prototype to paper in hours.

The practical implication: **worry less about who places the dot, more about whether the dots connect.** The accountability question (tracing which actor placed which dot) matters for debugging and correction — but it is an engineering concern, not a philosophical one about the value of discovery.

---

*This document is part of the SPL project's human×AI co-creation documentation.*
*Author: Wen Gong | AI partner: Claude | February 2026*
