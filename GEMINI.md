# SPL (Structured Prompt Language) - Project Context

SPL is a declarative, SQL-inspired language for LLM prompt engineering and context management. It treats LLMs as generative knowledge bases, providing automatic token budget optimization, built-in RAG, and persistent memory.

## Project Overview

- **Core Mission**: Standardize LLM prompt engineering with a SQL-like declarative syntax.
- **Key Features**:
  - **Token Budgeting**: Automatic allocation and truncation based on specified budgets.
  - **RAG (Retrieval-Augmented Generation)**: Built-in support for FAISS and ChromaDB.
  - **Persistent Memory**: SQLite-backed key-value store for cross-session context.
  - **Execution Plans**: `EXPLAIN` capability to visualize token allocation and costs.
  - **Provider Agnostic**: Adapters for Ollama (local), OpenRouter (cloud), and Claude CLI.
- **Architecture**: Lexer -> Parser (Recursive Descent) -> Analyzer -> Optimizer -> Executor.

## Tech Stack

- **Language**: Python 3.10+
- **CLI Framework**: Click
- **LLM Tokenization**: Tiktoken
- **Storage**: SQLite (Memory), FAISS/ChromaDB (Vector Store)
- **Async**: `asyncio` for parallel CTE (Common Table Expression) execution.
- **Testing**: `pytest`, `pytest-asyncio`

## Getting Started

### Installation

```bash
# Development install with all dependencies
pip install -e ".[dev,chroma]"
```

### Initializing a Workspace

```bash
spl init
```
This creates a `.spl/` directory with `config.yaml`, `memory.db`, and `vectors.faiss`.

### Basic Workflow

1.  **Validate**: `spl validate examples/hello_world.spl`
2.  **Explain**: `spl explain examples/hello_world.spl`
3.  **Execute**: `spl execute examples/hello_world.spl --params "question=How does SPL work?"`

## Development Conventions

- **Language Implementation**: Hand-written recursive descent parser in `spl/parser.py`. Avoid external parser generators.
- **Type Safety**: Use Python type hints throughout the codebase.
- **Logging**: Use the `dd-logging` wrapper (configured in `spl/cli.py`).
- **Adapters**: New LLM providers should implement the `LLMAdapter` base class in `spl/adapters/base.py`.
- **Storage**: Vector store backends should implement the `VectorStore` interface in `spl/storage/vector.py`.

## Testing and Benchmarks

### Running Tests

```bash
pytest
```

### Running Benchmarks

Benchmarks are located in `tests/benchmarks/` and should be run as modules:

```bash
python -m tests.benchmarks.bench_developer_experience
python -m tests.benchmarks.bench_token_optimization
python -m tests.benchmarks.bench_cost_estimation
python -m tests.benchmarks.bench_explain_showcase
python -m tests.benchmarks.bench_feature_verification
```

## Directory Structure

- `spl/`: Main package.
  - `lexer.py`, `parser.py`, `ast_nodes.py`: Language frontend.
  - `analyzer.py`, `optimizer.py`: Semantic analysis and token optimization.
  - `executor.py`: Execution engine and context gathering.
  - `adapters/`: LLM provider integrations (Ollama, OpenRouter, Claude).
  - `storage/`: SQLite (memory) and Vector (RAG) storage.
- `tests/`: Unit and integration tests.
  - `benchmarks/`: Performance and developer experience evaluation scripts.
- `examples/`: Sample `.spl` files demonstrating syntax and features.
- `docs/`: Design documents, grammar (EBNF), and co-creation logs.
