"""SPL Command-Line Interface.

Usage:
    spl init                          Initialize .spl/ directory
    spl validate <file.spl>          Parse + validate (no execution)
    spl explain <file.spl>           Show execution plan
    spl execute <file.spl> [--param k=v] [--adapter name] [--cache] [--no-log] Execute a query
    spl memory list                   List memory keys
    spl memory get <key>              Get memory value
    spl memory set <key> <value>      Set memory value
    spl rag add <file>                Index a file
    spl rag query "<text>"            Search vector store
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return

    command = args[0]

    if command == "init":
        _cmd_init()
    elif command == "validate":
        _cmd_validate(args[1:])
    elif command == "explain":
        _cmd_explain(args[1:])
    elif command == "execute":
        _cmd_execute(args[1:])
    elif command == "memory":
        _cmd_memory(args[1:])
    elif command == "rag":
        _cmd_rag(args[1:])
    elif command == "version":
        from spl import __version__
        print(f"spl-llm {__version__}")
    else:
        print(f"Unknown command: {command}")
        _print_help()
        sys.exit(1)


def _print_help():
    print("""SPL - Structured Prompt Language
SQL for LLM Context Management

Usage:
    spl init                              Initialize .spl/ directory
    spl validate <file.spl>              Validate SPL syntax
    spl explain <file.spl>               Show execution plan
    spl execute <file.spl> [--param k=v] [--adapter <name>] [--cache] [--no-log] Execute query
    spl memory list                       List memory keys
    spl memory get <key>                  Get value
    spl memory set <key> <value>          Set value
    spl rag add <file>                    Index file
    spl rag query "<text>" [--top-k N]    Search
    spl version                           Show version
""")


def _cmd_init():
    """Initialize .spl/ directory."""
    spl_dir = ".spl"
    os.makedirs(spl_dir, exist_ok=True)

    config_path = os.path.join(spl_dir, "config.yaml")
    if not os.path.exists(config_path):
        config_content = """# SPL Engine Configuration
# See: https://github.com/digital-duck/SPL

# LLM adapter: "claude_cli" (dev, subscription) or "openrouter" (production)
default_adapter: claude_cli

# Default model (leave empty to use adapter default)
# Examples: claude-sonnet-4-5, gpt-4o, anthropic/claude-sonnet-4-5
default_model: ""

# OpenRouter API key (required for openrouter adapter)
# Get yours at: https://openrouter.ai/keys
openrouter_api_key: ""

# Token budget defaults
defaults:
  budget: 8000
  output_budget: 4000
  temperature: 0.7

# Embedding model for RAG
embedding:
  model: default  # "default" uses built-in hash embedding; use "openrouter" for production
  dimensions: 384
"""
        with open(config_path, 'w') as f:
            f.write(config_content)

    print(f"Initialized SPL workspace in {os.path.abspath(spl_dir)}/")
    print(f"  Config: {config_path}")
    print(f"  Memory: {spl_dir}/memory.db (created on first use)")
    print(f"  Vectors: {spl_dir}/vectors.faiss (created on first use)")


def _cmd_validate(args: list[str]):
    """Validate SPL file."""
    if not args:
        print("Usage: spl validate <file.spl>")
        sys.exit(1)

    filepath = args[0]
    source = _read_file(filepath)

    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = Analyzer()
        result = analyzer.analyze(ast)

        print(f"OK: {filepath}")
        print(f"  Statements: {len(ast.statements)}")
        for stmt in ast.statements:
            print(f"  - {type(stmt).__name__}: {getattr(stmt, 'name', getattr(stmt, 'prompt_name', '?'))}")
        if result.warnings:
            print(f"  Warnings:")
            for w in result.warnings:
                print(f"    {w}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def _cmd_explain(args: list[str]):
    """Show execution plan."""
    if not args:
        print("Usage: spl explain <file.spl>")
        sys.exit(1)

    filepath = args[0]
    source = _read_file(filepath)

    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer
        from spl.optimizer import Optimizer
        from spl.explain import explain_plans

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = Analyzer()
        result = analyzer.analyze(ast)
        optimizer = Optimizer()
        plans = optimizer.optimize(result)

        if plans:
            print(explain_plans(plans))
        else:
            print("No PROMPT statements found to explain.")

        if result.warnings:
            print("\nAnalysis Warnings:")
            for w in result.warnings:
                print(f"  {w}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


_LOG_LEVELS = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING}


def _setup_logger(spl_filepath: str, adapter_name: str, log_level: str) -> logging.Logger:
    """Create a file logger: <script>-<adapter>-<datetime>.log under the SPL logs dir."""
    log_dir = Path("/home/papagame/projects/digital-duck/SPL/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    script_stem = Path(spl_filepath).stem          # e.g. "ri_family_v2"
    dt_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{script_stem}-{adapter_name}-{dt_str}.log"

    level = _LOG_LEVELS.get(log_level.lower(), logging.INFO)

    # Attach handler to the root "spl" logger so spl.executor logs also flow here
    spl_logger = logging.getLogger("spl")
    spl_logger.setLevel(logging.DEBUG)   # capture everything; handler filters

    # Remove stale handlers from previous runs in the same process
    spl_logger.handlers = [h for h in spl_logger.handlers
                           if not isinstance(h, logging.FileHandler)]

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
                                      datefmt="%H:%M:%S"))
    spl_logger.addHandler(fh)

    print(f"Logging to: {log_path}  (level={log_level})")
    return spl_logger


def _log(logger: logging.Logger | None, level: str, msg: str) -> None:
    if logger is None:
        return
    getattr(logger, level)(msg)


def _cmd_execute(args: list[str]):
    """Execute SPL query.

    Flags:
      --adapter <name>     LLM adapter: claude_cli (default), openrouter, ollama
      --cache              Enable SQLite result cache
      --no-log             Disable execution log (logging is on by default)
      --log-level <level>  Log verbosity: debug | info (default) | warning
    """
    if not args:
        print("Usage: spl execute <file.spl> [--param key=value ...] "
              "[--adapter name] [--cache] [--no-log] [--log-level debug|info|warning]")
        sys.exit(1)

    # Extract flags
    cache_enabled = "--cache"   in args
    log_enabled   = "--no-log" not in args
    args = [a for a in args if a not in ("--cache", "--no-log")]

    # Extract --adapter <name>
    adapter_name = "claude_cli"
    if "--adapter" in args:
        idx = args.index("--adapter")
        if idx + 1 < len(args):
            adapter_name = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --adapter requires a value (claude_cli | openrouter | ollama)")
            sys.exit(1)

    # Extract --log-level <level>
    log_level = "debug"
    if "--log-level" in args:
        idx = args.index("--log-level")
        if idx + 1 < len(args):
            log_level = args[idx + 1].lower()
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --log-level requires a value (debug | info | warning)")
            sys.exit(1)

    filepath = args[0]
    params = _parse_params(args[1:])
    source = _read_file(filepath)

    logger = _setup_logger(filepath, adapter_name, log_level) if log_enabled else None

    _log(logger, "info",  f"script  : {filepath}")
    _log(logger, "info",  f"adapter : {adapter_name}")
    _log(logger, "info",  f"cache   : {cache_enabled}")
    _log(logger, "info",  f"params  : {params}")

    t_total_start = time.perf_counter()

    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer
        from spl.optimizer import Optimizer
        from spl.executor import Executor
        from spl.ast_nodes import PromptStatement, CreateFunctionStatement

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = Analyzer()
        analysis = analyzer.analyze(ast)
        optimizer = Optimizer()
        plans = optimizer.optimize(analysis)

        if not plans:
            msg = "No PROMPT statements to execute."
            print(msg)
            _log(logger, "warning", msg)
            return

        executor = Executor(adapter_name=adapter_name, cache_enabled=cache_enabled)

        # Register any CREATE FUNCTION definitions
        for s in ast.statements:
            if isinstance(s, CreateFunctionStatement):
                executor.functions.register(s)
                _log(logger, "info", f"registered function: {s.name}")

        for plan in plans:
            stmt = None
            for s in ast.statements:
                if isinstance(s, PromptStatement) and s.name == plan.prompt_name:
                    stmt = s
                    break

            _log(logger, "info", f"executing prompt: {plan.prompt_name}")
            result = asyncio.run(executor.execute(plan, params=params, stmt=stmt))

            summary = (
                f"model={result.model}  "
                f"tokens={result.input_tokens}+{result.output_tokens}={result.total_tokens}  "
                f"latency={result.latency_ms:.0f}ms"
                + (f"  cost=${result.cost_usd:.5f}" if result.cost_usd else "")
            )
            _log(logger, "info",  f"completed: {plan.prompt_name}  {summary}")
            _log(logger, "debug", f"content:\n{result.content}")

            print(f"--- {plan.prompt_name} ---")
            print(result.content)
            print(f"\n[Model: {result.model} | "
                  f"Tokens: {result.input_tokens}+{result.output_tokens}={result.total_tokens} | "
                  f"Latency: {result.latency_ms:.0f}ms"
                  + (f" | Cost: ${result.cost_usd:.4f}" if result.cost_usd else "")
                  + "]")

        executor.close()

        total_s = time.perf_counter() - t_total_start
        _log(logger, "info", f"pipeline finished  total={total_s:.2f}s")

    except Exception as e:
        msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        _log(logger, "error", f"FAILED: {msg}")
        print(f"ERROR: {msg}")
        sys.exit(1)


def _cmd_memory(args: list[str]):
    """Memory operations."""
    if not args:
        print("Usage: spl memory [list|get|set|delete]")
        sys.exit(1)

    from spl.storage.memory import MemoryStore
    store = MemoryStore(".spl/memory.db")

    subcmd = args[0]

    if subcmd == "list":
        entries = store.list_all()
        if entries:
            print(f"{'Key':<30s} {'Tokens':>8s} {'Updated':<20s}")
            print("-" * 62)
            for e in entries:
                print(f"{e['key']:<30s} {e['tokens']:>8d} {e['updated_at']:<20s}")
        else:
            print("No memory entries.")

    elif subcmd == "get":
        if len(args) < 2:
            print("Usage: spl memory get <key>")
            sys.exit(1)
        value = store.get(args[1])
        if value is not None:
            print(value)
        else:
            print(f"Key '{args[1]}' not found.")
            sys.exit(1)

    elif subcmd == "set":
        if len(args) < 3:
            print("Usage: spl memory set <key> <value>")
            sys.exit(1)
        store.set(args[1], ' '.join(args[2:]))
        print(f"Stored: {args[1]}")

    elif subcmd == "delete":
        if len(args) < 2:
            print("Usage: spl memory delete <key>")
            sys.exit(1)
        if store.delete(args[1]):
            print(f"Deleted: {args[1]}")
        else:
            print(f"Key '{args[1]}' not found.")

    else:
        print(f"Unknown memory command: {subcmd}")

    store.close()


def _cmd_rag(args: list[str]):
    """RAG operations."""
    if not args:
        print("Usage: spl rag [add|query|count] [--backend faiss|chroma]")
        sys.exit(1)

    subcmd = args[0]

    # --backend flag (default: faiss)
    backend = "faiss"
    if "--backend" in args:
        idx = args.index("--backend")
        if idx + 1 < len(args):
            backend = args[idx + 1]

    from spl.storage import get_vector_store

    if subcmd == "add":
        if len(args) < 2:
            print("Usage: spl rag add <file> [--backend faiss|chroma]")
            sys.exit(1)
        filepath = args[1]
        text = _read_file(filepath)

        store = get_vector_store(backend, ".spl")

        # Chunk text into paragraphs
        chunks = [c.strip() for c in text.split('\n\n') if c.strip()]
        if not chunks:
            chunks = [text]

        ids = store.add_batch(
            chunks,
            [{"source": filepath, "chunk": i} for i in range(len(chunks))]
        )
        print(f"Indexed {len(ids)} chunks from {filepath} (backend: {backend})")
        print(f"Total documents: {store.count()}")
        store.close()

    elif subcmd == "query":
        if len(args) < 2:
            print("Usage: spl rag query \"<text>\" [--top-k N] [--backend faiss|chroma]")
            sys.exit(1)

        query_text = args[1]
        top_k = 5
        if "--top-k" in args:
            idx = args.index("--top-k")
            if idx + 1 < len(args):
                top_k = int(args[idx + 1])

        store = get_vector_store(backend, ".spl")

        results = store.query(query_text, top_k=top_k)
        if results:
            for r in results:
                meta = r.get("metadata", {})
                source = meta.get("source", "?")
                print(f"[Score: {r['score']:.4f} | Source: {source} | Tokens: {r['tokens']}]")
                print(r["text"][:200])
                print()
        else:
            print("No results found.")
        store.close()

    elif subcmd == "count":
        store = get_vector_store(backend, ".spl")
        print(f"Documents indexed: {store.count()} (backend: {backend})")
        store.close()

    else:
        print(f"Unknown rag command: {subcmd}")


def _read_file(filepath: str) -> str:
    """Read a file and return its contents."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as f:
        return f.read()


def _parse_params(args: list[str]) -> dict[str, str]:
    """Parse --param key=value arguments."""
    params = {}
    i = 0
    while i < len(args):
        if args[i] == "--param" and i + 1 < len(args):
            kv = args[i + 1]
            if "=" in kv:
                key, val = kv.split("=", 1)
                params[key] = val
            i += 2
        else:
            i += 1
    return params


if __name__ == "__main__":
    main()
