"""Tests for SPL Parser."""

import pytest
from spl.lexer import Lexer
from spl.parser import Parser, ParseError
from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement,
    ExplainStatement, ExecuteStatement,
    SystemRoleCall, ContextRef, RagQuery, MemoryGet,
    SelectItem, GenerateClause, StoreClause,
)


def parse(source: str) -> Program:
    """Helper: lex + parse."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class TestParserBasic:
    """Test basic parsing."""

    def test_minimal_prompt(self):
        ast = parse("""
            PROMPT hello
            SELECT system_role("helpful")
            GENERATE response()
        """)
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, PromptStatement)
        assert stmt.name == "hello"

    def test_prompt_with_budget(self):
        ast = parse("""
            PROMPT test
            WITH BUDGET 5000 tokens
            SELECT system_role("test")
            GENERATE response()
        """)
        stmt = ast.statements[0]
        assert stmt.budget == 5000

    def test_prompt_with_model(self):
        ast = parse("""
            PROMPT test
            USING MODEL claude-sonnet-4-5
            SELECT system_role("test")
            GENERATE response()
        """)
        stmt = ast.statements[0]
        assert "claude" in stmt.model

    def test_select_system_role(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("You are an expert")
            GENERATE response()
        """)
        items = ast.statements[0].select_items
        assert len(items) == 1
        assert isinstance(items[0].expression, SystemRoleCall)
        assert items[0].expression.description == "You are an expert"

    def test_select_context_ref(self):
        ast = parse("""
            PROMPT test
            SELECT context.user_data AS user LIMIT 500 tokens
            GENERATE response(user)
        """)
        items = ast.statements[0].select_items
        assert len(items) == 1
        assert isinstance(items[0].expression, ContextRef)
        assert items[0].expression.field_name == "user_data"
        assert items[0].alias == "user"
        assert items[0].limit_tokens == 500

    def test_select_rag_query(self):
        ast = parse("""
            PROMPT test
            SELECT rag.query("search text", top_k=3) AS docs LIMIT 2000 tokens
            GENERATE response(docs)
        """)
        items = ast.statements[0].select_items
        expr = items[0].expression
        assert isinstance(expr, RagQuery)
        assert expr.top_k == 3

    def test_select_memory_get(self):
        ast = parse("""
            PROMPT test
            SELECT memory.get("history") AS history LIMIT 300 tokens
            GENERATE response(history)
        """)
        items = ast.statements[0].select_items
        expr = items[0].expression
        assert isinstance(expr, MemoryGet)
        assert expr.key == "history"

    def test_multiple_select_items(self):
        ast = parse("""
            PROMPT test
            SELECT
                system_role("expert"),
                context.user AS user LIMIT 500 tokens,
                rag.query("docs", top_k=5) AS docs LIMIT 2000 tokens
            GENERATE response(user, docs)
        """)
        items = ast.statements[0].select_items
        assert len(items) == 3


class TestParserGenerate:
    """Test GENERATE clause parsing."""

    def test_generate_basic(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
        """)
        gen = ast.statements[0].generate_clause
        assert gen.function_name == "response"
        assert gen.arguments == []

    def test_generate_with_args(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test"), context.user AS user
            GENERATE detailed_response(user)
        """)
        gen = ast.statements[0].generate_clause
        assert gen.function_name == "detailed_response"
        assert len(gen.arguments) == 1

    def test_generate_with_options(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
            WITH OUTPUT BUDGET 2000 tokens, TEMPERATURE 0.3, FORMAT markdown
        """)
        gen = ast.statements[0].generate_clause
        assert gen.output_budget == 2000
        assert gen.temperature == 0.3
        assert gen.output_format == "markdown"


class TestParserWhere:
    """Test WHERE clause parsing."""

    def test_simple_where(self):
        ast = parse("""
            PROMPT test
            SELECT context.user AS user
            WHERE user.active = 1
            GENERATE response(user)
        """)
        where = ast.statements[0].where_clause
        assert where is not None
        assert len(where.conditions) == 1
        assert where.conditions[0].operator == "="

    def test_multiple_conditions(self):
        ast = parse("""
            PROMPT test
            SELECT context.user AS user
            WHERE user.active = 1 AND user.role = "admin"
            GENERATE response(user)
        """)
        where = ast.statements[0].where_clause
        assert len(where.conditions) == 2
        assert where.conjunctions == ["AND"]


class TestParserCTE:
    """Test CTE (WITH clause) parsing."""

    def test_single_cte(self):
        ast = parse("""
            PROMPT test
            WITH compressed AS (
                SELECT context.data AS data LIMIT 500 tokens
            )
            SELECT compressed
            GENERATE response(compressed)
        """)
        stmt = ast.statements[0]
        assert len(stmt.ctes) == 1
        assert stmt.ctes[0].name == "compressed"

    def test_multiple_ctes(self):
        ast = parse("""
            PROMPT test
            WITH profile AS (
                SELECT context.user AS user LIMIT 500 tokens
            ),
            docs AS (
                SELECT rag.query("docs", top_k=3) AS results LIMIT 2000 tokens
            )
            SELECT profile, docs
            GENERATE response(profile, docs)
        """)
        stmt = ast.statements[0]
        assert len(stmt.ctes) == 2
        assert stmt.ctes[0].name == "profile"
        assert stmt.ctes[1].name == "docs"


class TestParserStoreAndOther:
    """Test STORE, CREATE FUNCTION, EXPLAIN, EXECUTE."""

    def test_store_clause(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
            STORE RESULT IN memory.output
        """)
        store = ast.statements[0].store_clause
        assert store is not None
        assert store.key == "output"

    def test_explain(self):
        ast = parse("EXPLAIN PROMPT hello")
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], ExplainStatement)
        assert ast.statements[0].prompt_name == "hello"

    def test_create_function(self):
        ast = parse("""
            CREATE FUNCTION compress(text, max_tokens)
            RETURNS text
            AS $$ SELECT text LIMIT max_tokens tokens $$
        """)
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, CreateFunctionStatement)
        assert stmt.name == "compress"
        assert len(stmt.parameters) == 2

    def test_multiple_statements(self):
        ast = parse("""
            PROMPT first
            SELECT system_role("test")
            GENERATE response();

            PROMPT second
            SELECT system_role("test2")
            GENERATE response2()
        """)
        assert len(ast.statements) == 2
        assert ast.statements[0].name == "first"
        assert ast.statements[1].name == "second"


class TestParserExamples:
    """Test parsing the example .spl files."""

    def test_hello_world(self):
        source = """
        PROMPT hello_world
        WITH BUDGET 2000 tokens
        USING MODEL claude-sonnet-4-5
        SELECT
            system_role("You are a friendly assistant"),
            context.user_input AS input LIMIT 500 tokens
        GENERATE
            greeting(input)
        WITH OUTPUT BUDGET 1000 tokens
        """
        ast = parse(source)
        stmt = ast.statements[0]
        assert stmt.name == "hello_world"
        assert stmt.budget == 2000
        assert len(stmt.select_items) == 2
        assert stmt.generate_clause.output_budget == 1000
