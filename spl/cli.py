"""SPL Command-Line Interface.

Usage examples:
    spl init
    spl validate query.spl
    spl explain  query.spl
    spl execute  query.spl --params "doc=$(cat file.txt)" --adapter claude_cli
    spl execute  query.spl --output result.json --log myrun --log-level info
    spl memory list
    spl memory get  <key>
    spl memory set  <key> <value>
    spl memory delete <key>
    spl rag add    <file>  [--backend faiss|chroma]
    spl rag query  "<text>" [--top-k 5]
    spl rag count
    spl version
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

import click
from dd_logging import setup_logging as _dd_setup_logging

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_file(filepath: str) -> str:
    """Read a file and raise ClickException if not found."""
    path = Path(filepath)
    if not path.exists():
        raise click.ClickException(f"File not found: {filepath}")
    return path.read_text(encoding="utf-8")


def _parse_params_str(params_str: str) -> dict[str, str]:
    """Parse ``'k1=v1,k2=v2,...'`` (comma *or* space delimited) into a dict."""
    if not params_str:
        return {}
    params: dict[str, str] = {}
    parts = [p.strip() for p in params_str.replace(",", " ").split() if p.strip()]
    for part in parts:
        if "=" not in part:
            raise click.BadParameter(
                f"Expected key=value pair, got: {part!r}", param_hint="--params"
            )
        key, val = part.split("=", 1)
        params[key.strip()] = val.strip()
    return params


def _parse_models_str(models_str: str) -> list[str]:
    """Parse ``'m1,m2,...'`` (comma *or* space delimited) into a list."""
    if not models_str:
        return []
    return [m.strip() for m in models_str.replace(",", " ").split() if m.strip()]


def _setup_logger(
    run_name: str,
    adapter_name: str,
    log_level: str,
    log_file: str | None,
) -> logging.Logger:
    """Configure dd_logging and return the 'spl' root logger.

    If *log_file* is given its stem becomes the run_name and its parent the
    log_dir so the auto-timestamped file is placed where the user expects.
    """
    if log_file:
        p = Path(log_file)
        effective_name = p.stem
        effective_dir: Path | None = p.parent if str(p.parent) != "." else _LOG_DIR
    else:
        effective_name = run_name
        effective_dir = _LOG_DIR

    log_path = _dd_setup_logging(
        effective_name,
        root_name="spl",
        adapter=adapter_name,
        log_level=log_level,
        log_dir=effective_dir,
    )
    click.echo(f"Logging to: {log_path}  (level={log_level})")
    return logging.getLogger("spl")


def _infer_format(output_file: str, explicit_format: str | None) -> str:
    """Return output format: explicit_format if given, else inferred from extension."""
    if explicit_format:
        return explicit_format.lower()
    ext = Path(output_file).suffix.lower()
    return {".json": "json", ".csv": "csv", ".md": "markdown", ".txt": "text"}.get(
        ext, "text"
    )


def _write_output(data: object, output_file: str, fmt: str) -> None:
    """Serialise *data* to *output_file* in *fmt* format."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        content = json.dumps(data, indent=2, ensure_ascii=False)
    elif fmt == "csv":
        if isinstance(data, list) and all(isinstance(r, dict) for r in data):
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(data[0].keys()) if data else [])
            writer.writeheader()
            writer.writerows(data)  # type: ignore[arg-type]
            content = buf.getvalue()
        else:
            content = str(data)
    else:  # text / markdown
        content = str(data)

    path.write_text(content, encoding="utf-8")
    click.echo(f"Output written to: {output_file}")


# ── Shared option decorators ──────────────────────────────────────────────────

_adapter_opt = click.option(
    "--adapter", default="claude_cli", show_default=True,
    metavar="NAME",
    help="LLM adapter: claude_cli (default) | openrouter | ollama",
)
_log_opt = click.option(
    "--log", "log_file", default=None, metavar="FILE",
    help="Explicit log file path (stem used as run label; timestamped file created).",
)
_log_level_opt = click.option(
    "--log-level", default="debug", show_default=True,
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    help="Log verbosity.",
)
_no_log_flag = click.option(
    "--no-log", is_flag=True, default=False,
    help="Disable execution logging entirely.",
)


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="spl-llm", prog_name="spl")
def cli() -> None:
    """SPL — Structured Prompt Language.  SQL for LLM context management."""


# ── spl init ──────────────────────────────────────────────────────────────────

@cli.command("init")
def cmd_init() -> None:
    """Initialise .spl/ workspace in the current directory."""
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
        with open(config_path, "w") as fh:
            fh.write(config_content)

    click.echo(f"Initialized SPL workspace in {os.path.abspath(spl_dir)}/")
    click.echo(f"  Config:  {config_path}")
    click.echo(f"  Memory:  {spl_dir}/memory.db  (created on first use)")
    click.echo(f"  Vectors: {spl_dir}/vectors.faiss  (created on first use)")


# ── spl validate ──────────────────────────────────────────────────────────────

@cli.command("validate")
@click.argument("file", type=click.Path(dir_okay=False))
def cmd_validate(file: str) -> None:
    """Parse and validate FILE without executing."""
    source = _read_file(file)
    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        result = Analyzer().analyze(ast)

        click.echo(f"OK: {file}")
        click.echo(f"  Statements: {len(ast.statements)}")
        for stmt in ast.statements:
            click.echo(f"  - {type(stmt).__name__}: "
                       f"{getattr(stmt, 'name', getattr(stmt, 'prompt_name', '?'))}")
        if result.warnings:
            click.echo("  Warnings:")
            for w in result.warnings:
                click.echo(f"    {w}")

    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── spl explain ───────────────────────────────────────────────────────────────

@cli.command("explain")
@click.argument("file", type=click.Path(dir_okay=False))
@_log_opt
@_log_level_opt
@click.option("--output", "output_file", default=None, metavar="FILE",
              help="Write execution plan to FILE (format inferred from extension).")
def cmd_explain(file: str, log_file: str | None, log_level: str, output_file: str | None) -> None:
    """Show execution plan for FILE (no LLM call)."""
    if log_file:
        _setup_logger(
            run_name=Path(file).stem,
            adapter_name="",
            log_level=log_level,
            log_file=log_file,
        )

    source = _read_file(file)
    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer
        from spl.optimizer import Optimizer
        from spl.explain import explain_plans

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        result = Analyzer().analyze(ast)
        plans = Optimizer().optimize(result)

        lines: list[str] = []
        if plans:
            lines.append(explain_plans(plans))
        else:
            lines.append("No PROMPT statements found to explain.")

        if result.warnings:
            lines.append("\nAnalysis Warnings:")
            for w in result.warnings:
                lines.append(f"  {w}")

        output_text = "\n".join(lines)
        click.echo(output_text)

        if output_file:
            fmt = _infer_format(output_file, None)
            _write_output(output_text, output_file, fmt)

    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── spl execute ───────────────────────────────────────────────────────────────

@cli.command("execute")
@click.argument("file", type=click.Path(dir_okay=False))
@_adapter_opt
@click.option("--cache", is_flag=True, default=False,
              help="Enable SQLite result cache.")
@_no_log_flag
@_log_opt
@_log_level_opt
@click.option("--output", "output_file", default=None, metavar="FILE",
              help="Write result to FILE (format inferred from extension).")
@click.option("--format", "output_format",
              type=click.Choice(["json", "csv", "text", "markdown"], case_sensitive=False),
              default=None,
              help="Output format override (default: inferred from --output extension).")
@click.option("--params", "params_str", default="", metavar="K=V,...",
              help="Query parameters as comma-separated key=value pairs, "
                   "e.g. --params 'doc=hello,lang=fr'")
@click.option("--models", "models_str", default="", metavar="M1,M2,...",
              help="Override USING MODEL for each PROMPT (comma-separated). "
                   "Single value applies to all; multiple values cycle per PROMPT.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Print full JSON metrics for each PROMPT result.")
@click.option("--tools", "tools_str", default="", metavar="TOOL1,TOOL2,...",
              help="Comma-separated tools to allow the Claude CLI (e.g. 'WebSearch,WebFetch').")
@click.option("--claude-cli-timeout", "claude_cli_timeout", default=300, show_default=True,
              metavar="SECONDS",
              help="Timeout in seconds for each Claude CLI subprocess call.")
@click.option("--quiet", is_flag=True, default=False,
              help="Suppress progress output; print only the final result.")
def cmd_execute(
    file: str,
    adapter: str,
    cache: bool,
    no_log: bool,
    log_file: str | None,
    log_level: str,
    output_file: str | None,
    output_format: str | None,
    params_str: str,
    models_str: str,
    as_json: bool,
    tools_str: str,
    claude_cli_timeout: int,
    quiet: bool,
) -> None:
    """Execute FILE and print each PROMPT result."""
    params = _parse_params_str(params_str)
    model_overrides = _parse_models_str(models_str)
    allowed_tools = _parse_models_str(tools_str)  # same comma/space split logic
    source = _read_file(file)

    logger: logging.Logger | None = None
    if not no_log:
        logger = _setup_logger(
            run_name=Path(file).stem,
            adapter_name=adapter,
            log_level=log_level,
            log_file=log_file,
        )

    def _log(level: str, msg: str) -> None:
        if logger:
            getattr(logger, level)(msg)

    _log("info", f"script  : {file}")
    _log("info", f"adapter : {adapter}")
    _log("info", f"cache   : {cache}")
    _log("info", f"params  : {params}")
    if model_overrides:
        _log("info", f"models  : {model_overrides}")
    if allowed_tools:
        _log("info", f"tools   : {allowed_tools}")

    t_start = time.perf_counter()

    try:
        from spl.lexer import Lexer
        from spl.parser import Parser
        from spl.analyzer import Analyzer
        from spl.optimizer import Optimizer
        from spl.executor import Executor
        from spl.ast_nodes import PromptStatement, CreateFunctionStatement

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analysis = Analyzer().analyze(ast)
        plans = Optimizer().optimize(analysis)

        if not plans:
            click.echo("No PROMPT statements to execute.")
            _log("warning", "No PROMPT statements to execute.")
            return

        # Optional model override: patch USING MODEL clauses
        if model_overrides:
            import re
            for i, plan in enumerate(plans):
                model_id = model_overrides[i % len(model_overrides)]
                if model_id.lower() == "auto":
                    replacement = "USING MODEL auto"
                else:
                    replacement = f"USING MODEL '{model_id}'"
                source = re.sub(
                    r"USING\s+MODEL\s+(?:'[^']*'|\"[^\"]*\"|auto)",
                    replacement,
                    source,
                    flags=re.IGNORECASE,
                )
            # Re-parse with patched source
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            analysis = Analyzer().analyze(ast)
            plans = Optimizer().optimize(analysis)

        adapter_kwargs: dict = {}
        if allowed_tools:
            adapter_kwargs["allowed_tools"] = allowed_tools
        if adapter == "claude_cli":
            adapter_kwargs["timeout"] = claude_cli_timeout
        executor = Executor(
            adapter_name=adapter,
            cache_enabled=cache,
            adapter_kwargs=adapter_kwargs or None,
        )

        for stmt in ast.statements:
            if isinstance(stmt, CreateFunctionStatement):
                executor.functions.register(stmt)
                _log("info", f"registered function: {stmt.name}")

        all_results: list[dict] = []

        for plan in plans:
            prompt_stmt = next(
                (s for s in ast.statements
                 if isinstance(s, PromptStatement) and s.name == plan.prompt_name),
                None,
            )
            _log("info", f"executing prompt: {plan.prompt_name}")
            result = asyncio.run(executor.execute(plan, params=params, stmt=prompt_stmt))

            metrics_str = (
                f"model={result.model}  "
                f"tokens={result.input_tokens}+{result.output_tokens}={result.total_tokens}  "
                f"latency={result.latency_ms:.0f}ms"
                + (f"  cost=${result.cost_usd:.5f}" if result.cost_usd else "")
            )
            _log("info", f"completed: {plan.prompt_name}  {metrics_str}")
            _log("debug", f"content:\n{result.content}")

            run_dict = {
                "prompt_name": plan.prompt_name,
                "content": result.content,
                "model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "latency_ms": round(result.latency_ms, 1),
                "cost_usd": result.cost_usd,
            }
            all_results.append(run_dict)

            if as_json:
                click.echo(json.dumps(run_dict, indent=2, ensure_ascii=False))
            elif not quiet:
                click.echo(f"\n--- {plan.prompt_name} ---")
                click.echo(result.content)
                click.echo(
                    f"\n[Model: {result.model} | "
                    f"Tokens: {result.input_tokens}+{result.output_tokens}={result.total_tokens} | "
                    f"Latency: {result.latency_ms:.0f}ms"
                    + (f" | Cost: ${result.cost_usd:.4f}" if result.cost_usd else "")
                    + "]"
                )
            else:
                click.echo(result.content)

        executor.close()

        total_s = time.perf_counter() - t_start
        _log("info", f"pipeline finished  total={total_s:.2f}s")

        if output_file:
            fmt = _infer_format(output_file, output_format)
            payload: object = all_results if as_json or fmt == "json" else "\n\n".join(
                r["content"] for r in all_results
            )
            _write_output(payload, output_file, fmt)

    except click.ClickException:
        raise
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
        _log("error", f"FAILED: {msg}")
        raise click.ClickException(msg) from exc


# ── spl run (alias for execute) ───────────────────────────────────────────────

cli.add_command(cli.commands["execute"], name="run")


# ── spl memory ────────────────────────────────────────────────────────────────

@cli.group("memory")
def cmd_memory() -> None:
    """Manage the SPL persistent memory store (.spl/memory.db)."""


@cmd_memory.command("list")
def memory_list() -> None:
    """List all memory keys."""
    from spl.storage.memory import MemoryStore
    store = MemoryStore(".spl/memory.db")
    entries = store.list_all()
    if entries:
        click.echo(f"{'Key':<30s} {'Tokens':>8s} {'Updated':<20s}")
        click.echo("-" * 62)
        for e in entries:
            click.echo(f"{e['key']:<30s} {e['tokens']:>8d} {e['updated_at']:<20s}")
    else:
        click.echo("No memory entries.")
    store.close()


@cmd_memory.command("get")
@click.argument("key")
def memory_get(key: str) -> None:
    """Print the value stored under KEY."""
    from spl.storage.memory import MemoryStore
    store = MemoryStore(".spl/memory.db")
    value = store.get(key)
    store.close()
    if value is not None:
        click.echo(value)
    else:
        raise click.ClickException(f"Key '{key}' not found.")


@cmd_memory.command("set")
@click.argument("key")
@click.argument("value")
def memory_set(key: str, value: str) -> None:
    """Store VALUE under KEY."""
    from spl.storage.memory import MemoryStore
    store = MemoryStore(".spl/memory.db")
    store.set(key, value)
    store.close()
    click.echo(f"Stored: {key}")


@cmd_memory.command("delete")
@click.argument("key")
def memory_delete(key: str) -> None:
    """Delete KEY from the memory store."""
    from spl.storage.memory import MemoryStore
    store = MemoryStore(".spl/memory.db")
    deleted = store.delete(key)
    store.close()
    if deleted:
        click.echo(f"Deleted: {key}")
    else:
        raise click.ClickException(f"Key '{key}' not found.")


# ── spl rag ───────────────────────────────────────────────────────────────────

@cli.group("rag")
def cmd_rag() -> None:
    """Manage the SPL vector store for RAG (.spl/vectors)."""


_backend_opt = click.option(
    "--backend", default="faiss", show_default=True,
    type=click.Choice(["faiss", "chroma"], case_sensitive=False),
    help="Vector store backend.",
)


@cmd_rag.command("add")
@click.argument("file", type=click.Path(dir_okay=False))
@_backend_opt
def rag_add(file: str, backend: str) -> None:
    """Index FILE into the vector store."""
    from spl.storage import get_vector_store
    text = _read_file(file)
    store = get_vector_store(backend, ".spl")
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()] or [text]
    ids = store.add_batch(
        chunks,
        [{"source": file, "chunk": i} for i in range(len(chunks))],
    )
    click.echo(f"Indexed {len(ids)} chunks from {file}  (backend: {backend})")
    click.echo(f"Total documents: {store.count()}")
    store.close()


@cmd_rag.command("query")
@click.argument("text")
@click.option("--top-k", default=5, show_default=True, metavar="N",
              help="Number of results to return.")
@_backend_opt
def rag_query(text: str, top_k: int, backend: str) -> None:
    """Search the vector store for TEXT."""
    from spl.storage import get_vector_store
    store = get_vector_store(backend, ".spl")
    results = store.query(text, top_k=top_k)
    store.close()
    if results:
        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "?")
            click.echo(
                f"[Score: {r['score']:.4f} | Source: {source} | Tokens: {r['tokens']}]"
            )
            click.echo(r["text"][:200])
            click.echo()
    else:
        click.echo("No results found.")


@cmd_rag.command("count")
@_backend_opt
def rag_count(backend: str) -> None:
    """Show the number of indexed documents."""
    from spl.storage import get_vector_store
    store = get_vector_store(backend, ".spl")
    n = store.count()
    store.close()
    click.echo(f"Documents indexed: {n}  (backend: {backend})")


# ── spl version ───────────────────────────────────────────────────────────────

@cli.command("version")
def cmd_version() -> None:
    """Print the SPL engine version."""
    from spl import __version__
    click.echo(f"spl-llm {__version__}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Setuptools entry-point: delegates to the click CLI group."""
    cli()


if __name__ == "__main__":
    main()
