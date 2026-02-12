"""SPL Token types and Token dataclass."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    PROMPT = auto()
    WITH = auto()
    BUDGET = auto()
    TOKENS = auto()
    USING = auto()
    MODEL = auto()
    SELECT = auto()
    AS = auto()
    LIMIT = auto()
    WHERE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    ORDER = auto()
    BY = auto()
    ASC = auto()
    DESC = auto()
    GENERATE = auto()
    OUTPUT = auto()
    CREATE = auto()
    FUNCTION = auto()
    RETURNS = auto()
    EXPLAIN = auto()
    EXECUTE = auto()
    PARAMS = auto()
    STORE = auto()
    RESULT = auto()
    CACHE = auto()
    FOR = auto()
    FROM = auto()
    TEMPERATURE = auto()
    FORMAT = auto()
    BEGIN = auto()
    COMMIT = auto()
    ROLLBACK = auto()
    TRANSACTION = auto()
    ON = auto()
    ERROR = auto()
    AUTO_COMPRESS = auto()
    COMPRESSION_STRATEGY = auto()
    SCHEMA = auto()
    VERSION = auto()
    REFRESH = auto()
    EVERY = auto()
    MATERIALIZED = auto()

    # Built-in source identifiers (recognized during parsing, not lexing)
    # system_role, context, rag, memory are parsed as IDENTIFIER + DOT patterns

    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Operators
    DOT = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    EQ = auto()
    NEQ = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    STAR = auto()
    PLUS = auto()
    MINUS = auto()
    AT = auto()

    # Delimiters
    SEMICOLON = auto()
    DOLLAR_DOLLAR = auto()

    # Special
    EOF = auto()


# Map keyword strings to token types (case-insensitive)
KEYWORDS: dict[str, TokenType] = {
    "prompt": TokenType.PROMPT,
    "with": TokenType.WITH,
    "budget": TokenType.BUDGET,
    "tokens": TokenType.TOKENS,
    "using": TokenType.USING,
    "model": TokenType.MODEL,
    "select": TokenType.SELECT,
    "as": TokenType.AS,
    "limit": TokenType.LIMIT,
    "where": TokenType.WHERE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "in": TokenType.IN,
    "order": TokenType.ORDER,
    "by": TokenType.BY,
    "asc": TokenType.ASC,
    "desc": TokenType.DESC,
    "generate": TokenType.GENERATE,
    "output": TokenType.OUTPUT,
    "create": TokenType.CREATE,
    "function": TokenType.FUNCTION,
    "returns": TokenType.RETURNS,
    "explain": TokenType.EXPLAIN,
    "execute": TokenType.EXECUTE,
    "params": TokenType.PARAMS,
    "store": TokenType.STORE,
    "result": TokenType.RESULT,
    "cache": TokenType.CACHE,
    "for": TokenType.FOR,
    "from": TokenType.FROM,
    "temperature": TokenType.TEMPERATURE,
    "format": TokenType.FORMAT,
    "begin": TokenType.BEGIN,
    "commit": TokenType.COMMIT,
    "rollback": TokenType.ROLLBACK,
    "transaction": TokenType.TRANSACTION,
    "on": TokenType.ON,
    "error": TokenType.ERROR,
    "auto_compress": TokenType.AUTO_COMPRESS,
    "compression_strategy": TokenType.COMPRESSION_STRATEGY,
    "schema": TokenType.SCHEMA,
    "version": TokenType.VERSION,
    "refresh": TokenType.REFRESH,
    "every": TokenType.EVERY,
    "materialized": TokenType.MATERIALIZED,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
