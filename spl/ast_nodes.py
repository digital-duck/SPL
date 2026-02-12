"""SPL Abstract Syntax Tree node definitions."""

from __future__ import annotations
from dataclasses import dataclass, field


# === Expression Nodes ===

@dataclass
class Expression:
    """Base class for all expressions."""
    pass


@dataclass
class Literal(Expression):
    """String, integer, or float literal."""
    value: str | int | float
    literal_type: str  # "string", "integer", "float"


@dataclass
class Identifier(Expression):
    """Simple identifier (e.g., 'profile')."""
    name: str


@dataclass
class DottedName(Expression):
    """Dotted identifier (e.g., 'context.user_profile', 'docs.relevance')."""
    parts: list[str]

    @property
    def full_name(self) -> str:
        return '.'.join(self.parts)


@dataclass
class ParamRef(Expression):
    """Parameter reference (e.g., '@user_data')."""
    name: str


@dataclass
class FunctionCall(Expression):
    """Function call (e.g., 'summarize(text, 200)')."""
    name: str
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class BinaryOp(Expression):
    """Binary operation (e.g., 'a + b')."""
    left: Expression
    op: str  # "+", "-"
    right: Expression


@dataclass
class NamedArg(Expression):
    """Named argument in function call (e.g., 'top_k=5')."""
    name: str
    value: Expression


# === Source Expressions (SELECT item sources) ===

@dataclass
class SystemRoleCall(Expression):
    """system_role("description")."""
    description: str


@dataclass
class ContextRef(Expression):
    """context.<field> reference."""
    field_name: str


@dataclass
class RagQuery(Expression):
    """rag.query("search text", top_k=5)."""
    query_text: Expression
    top_k: int | None = None


@dataclass
class MemoryGet(Expression):
    """memory.get("key")."""
    key: str


# === Clause Nodes ===

@dataclass
class SelectItem:
    """Single item in a SELECT clause."""
    expression: Expression
    alias: str | None = None
    limit_tokens: int | None = None


@dataclass
class Condition:
    """Single condition in a WHERE clause."""
    left: Expression
    operator: str  # "=", "!=", ">", "<", ">=", "<=", "IN"
    right: Expression


@dataclass
class WhereClause:
    """WHERE clause with conditions joined by AND/OR."""
    conditions: list[Condition] = field(default_factory=list)
    conjunctions: list[str] = field(default_factory=list)  # "AND", "OR" between conditions


@dataclass
class OrderByItem:
    """Single item in ORDER BY."""
    expression: Expression
    direction: str = "ASC"  # "ASC" or "DESC"


@dataclass
class GenerateClause:
    """GENERATE function(args) WITH options."""
    function_name: str
    arguments: list[Expression] = field(default_factory=list)
    output_budget: int | None = None
    temperature: float | None = None
    output_format: str | None = None
    schema: str | None = None


@dataclass
class StoreClause:
    """STORE RESULT IN memory.<key>."""
    key: str


@dataclass
class FromClause:
    """FROM source AS alias."""
    source: Expression
    alias: str | None = None


# === CTE (Common Table Expression) ===

@dataclass
class CTEClause:
    """WITH <name> AS (...) common table expression."""
    name: str
    select_items: list[SelectItem] = field(default_factory=list)
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    limit_tokens: int | None = None


# === Top-Level Statements ===

@dataclass
class PromptStatement:
    """PROMPT <name> WITH BUDGET ... SELECT ... GENERATE ..."""
    name: str
    budget: int | None = None
    model: str | None = None
    cache_duration: str | None = None
    version: str | None = None
    ctes: list[CTEClause] = field(default_factory=list)
    select_items: list[SelectItem] = field(default_factory=list)
    where_clause: WhereClause | None = None
    order_by: list[OrderByItem] | None = None
    generate_clause: GenerateClause | None = None
    store_clause: StoreClause | None = None


@dataclass
class Parameter:
    """Function parameter definition."""
    name: str
    param_type: str | None = None


@dataclass
class CreateFunctionStatement:
    """CREATE FUNCTION <name>(...) RETURNS <type> AS $$ ... $$"""
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str = "text"
    body: str = ""


@dataclass
class ExplainStatement:
    """EXPLAIN PROMPT <name>."""
    prompt_name: str


@dataclass
class ExecuteStatement:
    """EXECUTE PROMPT <name> WITH PARAMS (...)."""
    prompt_name: str
    params: dict[str, Expression] = field(default_factory=dict)


@dataclass
class Program:
    """Top-level program node containing a list of statements."""
    statements: list[PromptStatement | CreateFunctionStatement | ExplainStatement | ExecuteStatement] = field(default_factory=list)
