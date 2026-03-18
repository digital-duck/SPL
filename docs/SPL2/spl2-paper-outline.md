# SPL 2.0: A Declarative Language for Agentic Workflow Orchestration

## Paper Outline

---

## Title

**SPL 2.0: A Declarative Language for Agentic Workflow Orchestration**

---

## Abstract (150-200 words)

We present SPL 2.0, a declarative language for orchestrating LLM-powered agentic workflows. Unlike existing imperative frameworks (LangGraph, AutoGen, CrewAI) that require Python programming and manual orchestration, SPL 2.0 enables users to express workflow intent through natural language — the universal interface accessible to both humans and machines. Our stack comprises four layers: (1) Natural Language as the interface layer, accepting multi-modal input; (2) text2SPL, a natural language compiler; (3) SPL 2.0, the declarative language with primitives for LLM-based evaluation, semantic iteration, and structured error handling; and (4) Momagrid, a decentralized execution runtime. SPL 2.0 introduces three key primitives absent in existing solutions: EVALUATE for LLM-judged condition evaluation, WHILE with semantic termination for iteration based on output quality, and EXCEPTION for structured handling of LLM-specific failures (hallucination, refusal, context overflow). The language is designed for compilation and optimization, enabling cost-based planning, automatic caching, and intelligent routing — capabilities impossible with imperative code. This unified approach eliminates the fragmentation of current LLM programming, providing a seamless path from natural language intent to human-consumable multi-modal output.

---

## 1. Introduction

### 1.1 The Problem: Fragmentation in LLM Programming
- Current state requires multiple skills and tools:
  - Prompt engineering for LLM interactions
  - Python programming for orchestration (LangGraph, AutoGen, CrewAI)
  - API wrangling for multiple model providers
  - Manual state management and error handling
- The "big data parallel": SQL + Python glue code all over again
- High barrier to entry: must be a programmer to build agentic systems

### 1.2 The Opportunity: Declarative Agentic Workflows
- What if expressing agentic intent was as simple as writing SQL?
- Declarative approach enables:
  - Optimization at the compiler level
  - Separation of "what" from "how"
  - Universal accessibility (not just programmers)

### 1.3 Our Contribution: The SPL Stack
- Four-layer architecture:
  1. Natural Language (interface) — multi-modal, universal
  2. text2SPL (compiler) — natural language to specification
  3. SPL 2.0 (specification) — declarative workflow language
  4. Momagrid (runtime) — decentralized execution
- Key primitives for agentic workflows:
  - EVALUATE: LLM-based condition evaluation
  - WHILE with semantic termination: iterate until "good enough"
  - EXCEPTION: structured error handling for LLM failures
- Three cross-cutting concerns built-in:
  - Compression (context efficiency)
  - Encryption (zero-trust security)
  - Accounting (economic incentives via Moma Points)

### 1.4 Paper Organization
- Roadmap of remaining sections

---

## 2. Motivation and Related Work

### 2.1 The Evolution of Data Programming
- SQL → PL/SQL pattern (Oracle's proven approach)
- Why declarative won: optimization, accessibility, standardization
- The gap PL/SQL filled: procedural logic around declarative queries

### 2.2 Current Approaches to Agentic Systems
- LangGraph: Graph-based state machines in Python
- AutoGen: Multi-agent conversations in Python
- CrewAI: Role-based agent teams in Python
- DSPy: Declarative but limited to prompt optimization
- Common limitation: All imperative, no compilation, no optimization

### 2.3 SQL Extensions and Their Limitations
- CTEs (Common Table Expressions): Limited iteration, no branching on computed results
- Recursive CTEs: Awkward, deterministic termination only
- Stored Procedures: Imperative but tied to specific databases
- Gap analysis: What's missing for LLM orchestration

### 2.4 Lessons from Proven Architectures
- Oracle: Block structure, exception handling, procedures, packages
- Apache Spark: Query planning, Catalyst optimizer, logical/physical plan separation
- JVM: Stable IR (bytecode), multiple frontends/backends, type system
- Synthesis: What SPL 2.0 should adopt

---

## 3. SPL 2.0 Language Design

### 3.1 Design Principles
- Declarative intent over imperative implementation
- LLM-aware primitives (evaluation, iteration, error handling)
- Compilation target (optimizable IR)
- Universal accessibility (works with natural language interface)

### 3.2 Core Primitives

#### 3.2.1 SELECT — Context Retrieval
- Retrieve context from knowledge sources
- Semantic matching, filtering, ranking
- Compression hints for large contexts

#### 3.2.2 GENERATE — LLM Invocation
- Invoke LLM to produce content
- Model selection, parameter tuning
- Output type annotations

#### 3.2.3 EVALUATE — LLM-Based Condition Evaluation
- Deterministic evaluation (score > 0.8)
- Semantic evaluation ('coherent', 'complete', 'accurate')
- Hybrid conditions
- The key primitive for agentic behavior

#### 3.2.4 WHILE...DO — Iteration with Semantic Termination
- Loop with LLM-judged termination
- Guard against infinite loops (max iterations)
- Context accumulation across iterations

#### 3.2.5 DO...END — Block Structure
- Scope management
- Context window isolation
- Error containment

#### 3.2.6 EXCEPTION — Structured Error Handling
- LLM-specific exceptions:
  - HallucinationDetected
  - RefusalToAnswer
  - ContextLengthExceeded
  - ModelOverloaded
  - QualityBelowThreshold
- Recovery strategies: RETRY, FALLBACK, COMMIT partial

#### 3.2.7 PROCEDURE — Reusable Workflow Patterns
- Parameterized workflows
- Composition and nesting
- Standard library: ReAct, Tree-of-Thought, Self-Refine

### 3.3 Cross-Cutting Concerns in Language Syntax

#### 3.3.1 Compression Hints
- Semantic compression for context
- Transmission compression for network
- Checkpoint compression for state

#### 3.3.2 Security Specifications
- Classification levels
- Encryption requirements
- Node policies (certification, region, trust level)

#### 3.3.3 Accounting Tags
- Billing attribution
- Budget limits
- Cost tracking

### 3.4 Formal Grammar (EBNF)
- Complete grammar specification
- Type system (optional but recommended)

---

## 4. Case Studies: Expressing Agentic Patterns in SPL 2.0

### 4.1 ReAct (Reasoning + Acting)
- Full workflow expressed in SPL 2.0
- Comparison with LangGraph implementation
- Lines of code, clarity, optimizability

### 4.2 Tree-of-Thought
- Multi-path exploration
- Evaluation and selection
- Backtracking expressed naturally

### 4.3 Self-Refine / Reflexion
- Iterative improvement loop
- Quality-based termination
- Critique generation and application

### 4.4 Multi-Agent Collaboration
- Role-based agent definition
- Communication patterns
- Shared state management

### 4.5 Real-World Example: Stock Analysis Workflow
- End-to-end demonstration
- Multi-modal input (documents, charts)
- Multi-modal output (report, recommendations)

---

## 5. Compilation and Optimization

### 5.1 The text2SPL Compiler
- Natural language parsing and understanding
- Intent extraction and workflow inference
- SPL 2.0 code generation

### 5.2 Intermediate Representation (IR)
- IR design goals: portable, optimizable, executable
- IR structure (JSON/Protobuf schema)
- Signing and encryption

### 5.3 Optimization Rules
- Merge adjacent GENERATEs (reduce LLM calls)
- Hoist deterministic conditions out of loops
- Cache repeated SELECTs
- Push down EVALUATE to cheapest executor
- Model selection optimization (cost vs. quality)

### 5.4 Logical Plan → Physical Plan
- Plan visualization (EXPLAIN command)
- Cost estimation
- Execution strategy selection

---

## 6. Momagrid Runtime Architecture

### 6.1 The Hub
- Workflow coordination
- State management (global context)
- Checkpointing and recovery
- Compression/Encryption/Accounting managers

### 6.2 GPU Nodes
- Stateless execution
- Secure enclave for decryption and inference
- Result encryption and reporting

### 6.3 Compression in Practice
- When and where to compress
- Compression ratio vs. information loss trade-offs
- Quality evaluation of compressed context

### 6.4 Encryption in Practice
- Zero-trust architecture
- Key hierarchy (Master → Session → Data)
- Node authentication and authorization

### 6.5 Accounting in Practice
- Event logging (who, what, when, where, why, how much)
- Moma Points calculation and distribution
- Reputation system for nodes

### 6.6 Hub ↔ Node Protocol
- Message formats
- Encryption handshake
- Error propagation

---

## 7. Evaluation

### 7.1 Expressiveness
- Can all major agentic patterns be expressed?
- Lines of code comparison with imperative frameworks
- Readability and maintainability

### 7.2 Performance
- Optimization impact (fewer LLM calls, better caching)
- Distributed execution benchmarks
- Comparison with LangGraph on standard tasks

### 7.3 Cost Efficiency
- Token usage optimization
- Automatic caching benefits
- Budget enforcement effectiveness

### 7.4 Developer Experience
- Time from intent to working workflow
- Barrier to entry (programmer vs. non-programmer)
- Debugging and observability

---

## 8. Discussion

### 8.1 Strengths
- Declarative approach enables optimization
- Natural language interface broadens accessibility
- Unified stack eliminates fragmentation
- Built-in cross-cutting concerns (compression, encryption, accounting)

### 8.2 Limitations
- Learning curve for SPL 2.0 syntax (mitigated by text2SPL)
- Compiler complexity
- Distributed system challenges

### 8.3 Future Work
- Visual workflow builder
- Extended procedure library
- Multi-modal input processing improvements
- Fine-tuned text2SPL models
- Formal verification of workflow properties

---

## 9. Conclusion

- SPL 2.0 represents a paradigm shift from imperative to declarative agentic workflows
- The four-layer stack (Natural Language → text2SPL → SPL 2.0 → Momagrid) provides a unified path from intent to output
- Key primitives (EVALUATE, semantic WHILE, EXCEPTION) address LLM-specific needs not met by SQL extensions
- Declarative design enables optimization impossible in imperative frameworks
- Universal accessibility: humans and machines both use natural language as the interface

---

## Appendix A: Complete SPL 2.0 Grammar (EBNF)

## Appendix B: IR Specification (JSON Schema)

## Appendix C: Exception Type Hierarchy

## Appendix D: Standard Procedure Library

## Appendix E: Hub ↔ Node Protocol Specification

---

## Key Figures

1. Four-layer architecture diagram
2. Imperative vs. Declarative comparison
3. EVALUATE primitive enabling agency
4. Compilation pipeline (Natural Language → IR → Physical Plan)
5. Momagrid runtime architecture
6. Hub ↔ Node protocol flow
7. Compression touchpoints
8. Encryption layers
9. Accounting event structure

## Key Tables

1. Capability comparison: CTE vs. SPL 2.0
2. Design principles from proven architectures
3. Exception type hierarchy
4. Optimization rules catalog
5. Moma Points reward calculation
