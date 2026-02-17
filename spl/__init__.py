"""
SPL - Structured Prompt Language
SQL-inspired declarative language for LLM context management.

Treats LLMs as generative knowledge bases with automatic token budget
optimization, built-in RAG (FAISS), and persistent memory (SQLite).
"""

__version__ = "0.1.0"

from spl.lexer import Lexer
from spl.parser import Parser
from spl.analyzer import Analyzer
from spl.optimizer import Optimizer
from spl.executor import Executor
from spl.explain import explain_plan, explain_plans


def parse(source: str):
    """Parse SPL source into AST."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def validate(source: str):
    """Parse and semantically validate SPL source."""
    ast = parse(source)
    analyzer = Analyzer()
    return analyzer.analyze(ast)


def explain(source: str) -> str:
    """Parse, optimize, and return EXPLAIN plan as string."""
    ast = parse(source)
    analyzer = Analyzer()
    analyzed = analyzer.analyze(ast)
    optimizer = Optimizer()
    plans = optimizer.optimize(analyzed)   # returns list[ExecutionPlan]
    return explain_plans(plans)


async def execute(source: str, params: dict | None = None, adapter: str = "claude_cli"):
    """Parse, optimize, and execute SPL query."""
    ast = parse(source)
    analyzer = Analyzer()
    analyzed = analyzer.analyze(ast)
    optimizer = Optimizer()
    plan = optimizer.optimize(analyzed)
    executor = Executor(adapter_name=adapter)
    return await executor.execute(plan, params=params or {})
