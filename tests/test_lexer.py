"""Tests for SPL Lexer."""

import pytest
from spl.lexer import Lexer, LexerError
from spl.tokens import TokenType


class TestLexer:
    """Test the SPL lexer."""

    def test_simple_prompt(self):
        source = 'PROMPT hello'
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.PROMPT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "hello"
        assert tokens[2].type == TokenType.EOF

    def test_keywords_case_insensitive(self):
        source = 'prompt HELLO select WHERE'
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.PROMPT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[2].type == TokenType.SELECT
        assert tokens[3].type == TokenType.WHERE

    def test_string_literals(self):
        source = '"hello world" \'single quotes\''
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "single quotes"

    def test_integer_literal(self):
        source = "42 1000"
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.INTEGER
        assert tokens[1].value == "1000"

    def test_float_literal(self):
        source = "3.14 0.7"
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.FLOAT
        assert tokens[0].value == "3.14"
        assert tokens[1].type == TokenType.FLOAT
        assert tokens[1].value == "0.7"

    def test_operators(self):
        source = ". , ( ) = != > < >= <="
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens[:-1]]  # exclude EOF
        assert types == [
            TokenType.DOT, TokenType.COMMA,
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.EQ, TokenType.NEQ,
            TokenType.GT, TokenType.LT,
            TokenType.GTE, TokenType.LTE,
        ]

    def test_comments_skipped(self):
        source = """
        -- This is a comment
        PROMPT hello
        -- Another comment
        SELECT
        """
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [TokenType.PROMPT, TokenType.IDENTIFIER, TokenType.SELECT]

    def test_dollar_dollar(self):
        source = '$$ body $$'
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.DOLLAR_DOLLAR
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "body"
        assert tokens[2].type == TokenType.DOLLAR_DOLLAR

    def test_dot_notation(self):
        source = "context.user"
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "context"
        assert tokens[1].type == TokenType.DOT
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "user"

    def test_with_budget(self):
        source = "WITH BUDGET 8000 TOKENS"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.WITH, TokenType.BUDGET, TokenType.INTEGER, TokenType.TOKENS]

    def test_line_tracking(self):
        source = "PROMPT\nhello"
        tokens = Lexer(source).tokenize()
        assert tokens[0].line == 1
        assert tokens[1].line == 2

    def test_at_symbol(self):
        source = "@user_data"
        tokens = Lexer(source).tokenize()
        assert tokens[0].type == TokenType.AT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "user_data"

    def test_unterminated_string(self):
        with pytest.raises(LexerError, match="Unterminated"):
            Lexer('"hello').tokenize()

    def test_full_prompt_query(self):
        source = """
        PROMPT hello_world
        WITH BUDGET 2000 tokens
        USING MODEL claude-sonnet-4-5
        SELECT
            system_role("You are helpful"),
            context.input AS user_input LIMIT 500 tokens
        GENERATE
            response(user_input)
        WITH OUTPUT BUDGET 1000 tokens;
        """
        tokens = Lexer(source).tokenize()
        # Should tokenize without error
        assert tokens[-1].type == TokenType.EOF
        # Check we got meaningful tokens
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.PROMPT in types
        assert TokenType.SELECT in types
        assert TokenType.GENERATE in types
