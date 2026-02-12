"""SPL Parser: hand-written recursive descent parser producing AST from tokens."""

from spl.tokens import Token, TokenType
from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement, ExplainStatement,
    ExecuteStatement, SelectItem, CTEClause, WhereClause, Condition,
    OrderByItem, GenerateClause, StoreClause, FromClause, Parameter,
    Expression, Literal, Identifier, DottedName, ParamRef, FunctionCall,
    BinaryOp, NamedArg, SystemRoleCall, ContextRef, RagQuery, MemoryGet,
)


class ParseError(Exception):
    """Raised when the parser encounters unexpected tokens."""

    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Parse error at {token.line}:{token.column}: {message}")


class Parser:
    """Recursive descent parser for SPL."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        """Parse the full program."""
        statements = []
        while not self._check(TokenType.EOF):
            stmt = self._parse_statement()
            statements.append(stmt)
            # Optional semicolons between statements
            while self._check(TokenType.SEMICOLON):
                self._advance()
        return Program(statements=statements)

    # === Statement Dispatch ===

    def _parse_statement(self):
        if self._check(TokenType.PROMPT):
            return self._parse_prompt_statement()
        elif self._check(TokenType.CREATE):
            return self._parse_create_function()
        elif self._check(TokenType.EXPLAIN):
            return self._parse_explain()
        elif self._check(TokenType.EXECUTE):
            return self._parse_execute()
        else:
            raise ParseError(
                f"Expected PROMPT, CREATE, EXPLAIN, or EXECUTE, got {self._current().type.name}",
                self._current()
            )

    # === PROMPT Statement ===

    def _parse_prompt_statement(self) -> PromptStatement:
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value

        # Parse optional header clauses
        budget = None
        model = None
        cache_duration = None
        version = None

        # WITH BUDGET <n> TOKENS
        if self._check(TokenType.WITH) and self._peek_is(TokenType.BUDGET):
            self._advance()  # WITH
            self._advance()  # BUDGET
            budget = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        # USING MODEL <name>
        # Model names can contain hyphens and numbers: claude-sonnet-4-5
        if self._check(TokenType.USING):
            self._advance()
            self._expect(TokenType.MODEL)
            if self._check(TokenType.STRING):
                model = self._advance().value
            else:
                model = self._read_model_name()

        # CACHE FOR <duration>
        if self._check(TokenType.CACHE):
            self._advance()
            self._expect(TokenType.FOR)
            dur_val = self._expect(TokenType.INTEGER).value
            dur_unit = self._expect(TokenType.IDENTIFIER).value
            cache_duration = f"{dur_val} {dur_unit}"

        # VERSION <version>
        if self._check(TokenType.VERSION):
            self._advance()
            if self._check(TokenType.FLOAT):
                version = self._advance().value
            elif self._check(TokenType.INTEGER):
                version = self._advance().value
            else:
                version = self._expect(TokenType.STRING).value

        # Parse optional CTEs: WITH <name> AS (...)
        ctes = []
        if self._check(TokenType.WITH) and not self._peek_is(TokenType.BUDGET):
            ctes = self._parse_cte_block()

        # Parse SELECT clause
        select_items = self._parse_select_clause()

        # Parse optional WHERE clause
        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        # Parse optional ORDER BY clause
        order_by = None
        if self._check(TokenType.ORDER):
            order_by = self._parse_order_by()

        # Parse GENERATE clause
        generate_clause = None
        if self._check(TokenType.GENERATE):
            generate_clause = self._parse_generate_clause()

        # Parse optional STORE clause
        store_clause = None
        if self._check(TokenType.STORE):
            store_clause = self._parse_store_clause()

        return PromptStatement(
            name=name,
            budget=budget,
            model=model,
            cache_duration=cache_duration,
            version=version,
            ctes=ctes,
            select_items=select_items,
            where_clause=where_clause,
            order_by=order_by,
            generate_clause=generate_clause,
            store_clause=store_clause,
        )

    # === CTE Block ===

    def _parse_cte_block(self) -> list[CTEClause]:
        self._expect(TokenType.WITH)
        ctes = [self._parse_cte_def()]
        while self._check(TokenType.COMMA):
            self._advance()
            ctes.append(self._parse_cte_def())
        return ctes

    def _parse_cte_def(self) -> CTEClause:
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.AS)
        self._expect(TokenType.LPAREN)

        select_items = self._parse_select_clause()

        from_clause = None
        if self._check(TokenType.FROM):
            from_clause = self._parse_from_clause()

        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        limit_tokens = None
        if self._check(TokenType.LIMIT):
            self._advance()
            limit_tokens = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        self._expect(TokenType.RPAREN)

        return CTEClause(
            name=name,
            select_items=select_items,
            from_clause=from_clause,
            where_clause=where_clause,
            limit_tokens=limit_tokens,
        )

    # === SELECT Clause ===

    def _parse_select_clause(self) -> list[SelectItem]:
        self._expect(TokenType.SELECT)
        items = [self._parse_select_item()]
        while self._check(TokenType.COMMA):
            self._advance()
            # Stop if next token is a clause keyword (not another select item)
            if self._check_any(TokenType.WHERE, TokenType.ORDER, TokenType.GENERATE,
                               TokenType.STORE, TokenType.LIMIT, TokenType.RPAREN):
                break
            items.append(self._parse_select_item())
        return items

    def _parse_select_item(self) -> SelectItem:
        expr = self._parse_source_expression()

        alias = None
        if self._check(TokenType.AS):
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value

        limit_tokens = None
        if self._check(TokenType.LIMIT):
            self._advance()
            limit_tokens = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        return SelectItem(expression=expr, alias=alias, limit_tokens=limit_tokens)

    def _parse_source_expression(self) -> Expression:
        """Parse a source expression: system_role(), context.*, rag.query(), memory.get(), or identifier."""
        tok = self._current()

        # system_role("...")
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "system_role":
            self._advance()
            self._expect(TokenType.LPAREN)
            desc = self._expect(TokenType.STRING).value
            self._expect(TokenType.RPAREN)
            return SystemRoleCall(description=desc)

        # context.<field>
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "context":
            self._advance()
            self._expect(TokenType.DOT)
            field_name = self._expect(TokenType.IDENTIFIER).value
            return ContextRef(field_name=field_name)

        # rag.query("...", top_k=N)
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "rag":
            self._advance()
            self._expect(TokenType.DOT)
            method = self._expect(TokenType.IDENTIFIER)
            if method.value.lower() != "query":
                raise ParseError(f"Expected 'query' after 'rag.', got '{method.value}'", method)
            self._expect(TokenType.LPAREN)
            query_text = self._parse_expression()
            top_k = None
            if self._check(TokenType.COMMA):
                self._advance()
                # top_k = N
                arg_name = self._expect(TokenType.IDENTIFIER)
                if arg_name.value.lower() != "top_k":
                    raise ParseError(f"Expected 'top_k', got '{arg_name.value}'", arg_name)
                self._expect(TokenType.EQ)
                top_k = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.RPAREN)
            return RagQuery(query_text=query_text, top_k=top_k)

        # memory.get("key")
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "memory":
            self._advance()
            self._expect(TokenType.DOT)
            method = self._expect(TokenType.IDENTIFIER)
            if method.value.lower() != "get":
                raise ParseError(f"Expected 'get' after 'memory.', got '{method.value}'", method)
            self._expect(TokenType.LPAREN)
            key = self._expect(TokenType.STRING).value
            self._expect(TokenType.RPAREN)
            return MemoryGet(key=key)

        # General identifier, dotted name, or function call
        return self._parse_expression()

    # === FROM Clause ===

    def _parse_from_clause(self) -> FromClause:
        self._expect(TokenType.FROM)
        source = self._parse_source_expression()
        alias = None
        if self._check(TokenType.AS):
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value
        return FromClause(source=source, alias=alias)

    # === WHERE Clause ===

    def _parse_where_clause(self) -> WhereClause:
        self._expect(TokenType.WHERE)
        conditions = [self._parse_condition()]
        conjunctions = []

        while self._check_any(TokenType.AND, TokenType.OR):
            conj = self._advance().type.name
            conjunctions.append(conj)
            conditions.append(self._parse_condition())

        return WhereClause(conditions=conditions, conjunctions=conjunctions)

    def _parse_condition(self) -> Condition:
        left = self._parse_expression()

        # Comparator
        op_map = {
            TokenType.EQ: "=",
            TokenType.NEQ: "!=",
            TokenType.GT: ">",
            TokenType.LT: "<",
            TokenType.GTE: ">=",
            TokenType.LTE: "<=",
            TokenType.IN: "IN",
        }

        tok = self._current()
        if tok.type not in op_map:
            raise ParseError(
                f"Expected comparison operator, got {tok.type.name}", tok
            )
        op = op_map[tok.type]
        self._advance()

        if op == "IN":
            self._expect(TokenType.LPAREN)
            values = [self._parse_expression()]
            while self._check(TokenType.COMMA):
                self._advance()
                values.append(self._parse_expression())
            self._expect(TokenType.RPAREN)
            # Represent IN as right side being a function call with values
            right = FunctionCall(name="__in_list__", arguments=values)
        else:
            right = self._parse_expression()

        return Condition(left=left, operator=op, right=right)

    # === ORDER BY ===

    def _parse_order_by(self) -> list[OrderByItem]:
        self._expect(TokenType.ORDER)
        self._expect(TokenType.BY)
        items = [self._parse_order_item()]
        while self._check(TokenType.COMMA):
            self._advance()
            items.append(self._parse_order_item())
        return items

    def _parse_order_item(self) -> OrderByItem:
        expr = self._parse_expression()
        direction = "ASC"
        if self._check(TokenType.ASC):
            self._advance()
            direction = "ASC"
        elif self._check(TokenType.DESC):
            self._advance()
            direction = "DESC"
        return OrderByItem(expression=expr, direction=direction)

    # === GENERATE Clause ===

    def _parse_generate_clause(self) -> GenerateClause:
        self._expect(TokenType.GENERATE)
        func_name = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.LPAREN)
        arguments: list[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_expression())
            while self._check(TokenType.COMMA):
                self._advance()
                arguments.append(self._parse_expression())
        self._expect(TokenType.RPAREN)

        # Parse optional WITH OUTPUT BUDGET, TEMPERATURE, FORMAT
        output_budget = None
        temperature = None
        output_format = None
        schema = None

        if self._check(TokenType.WITH):
            self._advance()
            while True:
                if self._check(TokenType.OUTPUT):
                    self._advance()
                    self._expect(TokenType.BUDGET)
                    output_budget = int(self._expect(TokenType.INTEGER).value)
                    self._expect(TokenType.TOKENS)
                elif self._check(TokenType.TEMPERATURE):
                    self._advance()
                    if self._check(TokenType.FLOAT):
                        temperature = float(self._advance().value)
                    else:
                        temperature = float(self._expect(TokenType.INTEGER).value)
                elif self._check(TokenType.FORMAT):
                    self._advance()
                    output_format = self._expect(TokenType.IDENTIFIER).value
                elif self._check(TokenType.SCHEMA):
                    self._advance()
                    schema = self._expect(TokenType.IDENTIFIER).value
                else:
                    break

                if self._check(TokenType.COMMA):
                    self._advance()
                else:
                    break

        return GenerateClause(
            function_name=func_name,
            arguments=arguments,
            output_budget=output_budget,
            temperature=temperature,
            output_format=output_format,
            schema=schema,
        )

    # === STORE Clause ===

    def _parse_store_clause(self) -> StoreClause:
        self._expect(TokenType.STORE)
        self._expect(TokenType.RESULT)
        self._expect(TokenType.IN)

        # Expect memory.<key>
        mem_tok = self._expect(TokenType.IDENTIFIER)
        if mem_tok.value.lower() != "memory":
            raise ParseError(f"Expected 'memory' after STORE RESULT IN, got '{mem_tok.value}'", mem_tok)
        self._expect(TokenType.DOT)
        # Key might be a keyword used as identifier (e.g., "output", "result")
        key = self._expect_identifier_or_keyword().value

        return StoreClause(key=key)

    # === CREATE FUNCTION ===

    def _parse_create_function(self) -> CreateFunctionStatement:
        self._expect(TokenType.CREATE)
        self._expect(TokenType.FUNCTION)
        name = self._expect(TokenType.IDENTIFIER).value

        # Parameters
        self._expect(TokenType.LPAREN)
        parameters: list[Parameter] = []
        if not self._check(TokenType.RPAREN):
            parameters.append(self._parse_parameter())
            while self._check(TokenType.COMMA):
                self._advance()
                parameters.append(self._parse_parameter())
        self._expect(TokenType.RPAREN)

        # RETURNS type
        self._expect(TokenType.RETURNS)
        return_type = self._expect(TokenType.IDENTIFIER).value

        # AS $$ body $$
        self._expect(TokenType.AS)
        self._expect(TokenType.DOLLAR_DOLLAR)

        # Collect everything between $$ and $$ as the body text
        body_tokens: list[str] = []
        while not self._check(TokenType.DOLLAR_DOLLAR) and not self._check(TokenType.EOF):
            body_tokens.append(self._advance().value)
        body = ' '.join(body_tokens)

        self._expect(TokenType.DOLLAR_DOLLAR)

        return CreateFunctionStatement(
            name=name,
            parameters=parameters,
            return_type=return_type,
            body=body,
        )

    def _parse_parameter(self) -> Parameter:
        name = self._expect(TokenType.IDENTIFIER).value
        param_type = None
        # Optional type annotation
        if self._check(TokenType.IDENTIFIER) and not self._check(TokenType.COMMA) and not self._check(TokenType.RPAREN):
            param_type = self._advance().value
        return Parameter(name=name, param_type=param_type)

    # === EXPLAIN ===

    def _parse_explain(self) -> ExplainStatement:
        self._expect(TokenType.EXPLAIN)
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value
        return ExplainStatement(prompt_name=name)

    # === EXECUTE ===

    def _parse_execute(self) -> ExecuteStatement:
        self._expect(TokenType.EXECUTE)
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value

        params: dict[str, Expression] = {}
        if self._check(TokenType.WITH):
            self._advance()
            self._expect(TokenType.PARAMS)
            self._expect(TokenType.LPAREN)

            if not self._check(TokenType.RPAREN):
                key, val = self._parse_param_assignment()
                params[key] = val
                while self._check(TokenType.COMMA):
                    self._advance()
                    key, val = self._parse_param_assignment()
                    params[key] = val

            self._expect(TokenType.RPAREN)

        return ExecuteStatement(prompt_name=name, params=params)

    def _parse_param_assignment(self) -> tuple[str, Expression]:
        """Parse context.field = @value or key = value."""
        parts = [self._expect(TokenType.IDENTIFIER).value]
        while self._check(TokenType.DOT):
            self._advance()
            parts.append(self._expect(TokenType.IDENTIFIER).value)
        key = '.'.join(parts)
        self._expect(TokenType.EQ)
        value = self._parse_expression()
        return key, value

    # === Expression Parsing ===

    def _parse_expression(self) -> Expression:
        """Parse an expression with optional +/- operations."""
        left = self._parse_primary()

        while self._check_any(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_primary()
            left = BinaryOp(left=left, op=op, right=right)

        return left

    def _parse_primary(self) -> Expression:
        """Parse a primary expression."""
        tok = self._current()

        # @param reference
        if tok.type == TokenType.AT:
            self._advance()
            name = self._expect(TokenType.IDENTIFIER).value
            return ParamRef(name=name)

        # String literal
        if tok.type == TokenType.STRING:
            self._advance()
            return Literal(value=tok.value, literal_type="string")

        # Integer literal
        if tok.type == TokenType.INTEGER:
            self._advance()
            return Literal(value=int(tok.value), literal_type="integer")

        # Float literal
        if tok.type == TokenType.FLOAT:
            self._advance()
            return Literal(value=float(tok.value), literal_type="float")

        # Identifier (possibly dotted, possibly function call)
        if tok.type == TokenType.IDENTIFIER:
            return self._parse_identifier_expression()

        # Keywords used as identifiers in expression context
        if tok.type in (TokenType.FORMAT, TokenType.MODEL, TokenType.RESULT,
                        TokenType.VERSION, TokenType.SCHEMA, TokenType.ERROR):
            self._advance()
            return Identifier(name=tok.value)

        raise ParseError(f"Expected expression, got {tok.type.name} ({tok.value!r})", tok)

    def _parse_identifier_expression(self) -> Expression:
        """Parse an identifier that might be dotted or a function call."""
        name = self._advance().value  # consume identifier

        # Function call: name(...)
        if self._check(TokenType.LPAREN):
            self._advance()  # (
            args: list[Expression] = []
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_call_argument())
                while self._check(TokenType.COMMA):
                    self._advance()
                    args.append(self._parse_call_argument())
            self._expect(TokenType.RPAREN)
            return FunctionCall(name=name, arguments=args)

        # Dotted name: name.field.subfield
        if self._check(TokenType.DOT):
            parts = [name]
            while self._check(TokenType.DOT):
                self._advance()
                parts.append(self._expect(TokenType.IDENTIFIER).value)
            return DottedName(parts=parts)

        return Identifier(name=name)

    def _parse_call_argument(self) -> Expression:
        """Parse a function argument, which might be a named arg (key=value)."""
        # Try to detect named argument: IDENT = expr
        if (self._check(TokenType.IDENTIFIER)
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.EQ):
            name = self._advance().value
            self._advance()  # =
            value = self._parse_expression()
            return NamedArg(name=name, value=value)
        return self._parse_expression()

    # === Token Helpers ===

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)

    def _advance(self) -> Token:
        tok = self._current()
        self.pos += 1
        return tok

    def _check(self, token_type: TokenType) -> bool:
        return self._current().type == token_type

    def _check_any(self, *token_types: TokenType) -> bool:
        return self._current().type in token_types

    def _peek_is(self, token_type: TokenType) -> bool:
        """Check if the token after current is the given type."""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].type == token_type
        return False

    def _expect(self, token_type: TokenType) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise ParseError(
                f"Expected {token_type.name}, got {tok.type.name} ({tok.value!r})",
                tok
            )
        return self._advance()

    def _expect_identifier_or_keyword(self) -> Token:
        """Expect an IDENTIFIER or accept a keyword token used as identifier."""
        tok = self._current()
        if tok.type == TokenType.IDENTIFIER:
            return self._advance()
        # Accept keywords as identifiers in certain contexts
        # (e.g., memory.output where 'output' is a keyword)
        if tok.type in (TokenType.OUTPUT, TokenType.RESULT, TokenType.FORMAT,
                        TokenType.MODEL, TokenType.VERSION, TokenType.SCHEMA,
                        TokenType.ERROR, TokenType.STORE, TokenType.CACHE,
                        TokenType.BUDGET, TokenType.LIMIT):
            return self._advance()
        raise ParseError(
            f"Expected identifier, got {tok.type.name} ({tok.value!r})", tok
        )

    def _read_model_name(self) -> str:
        """Read a model name that may contain hyphens and numbers.

        e.g., claude-sonnet-4-5, gpt-4o, llama-3.1-70b
        """
        parts = []
        # First part must be an identifier
        parts.append(self._expect(TokenType.IDENTIFIER).value)
        # Continue consuming MINUS + (IDENTIFIER | INTEGER | FLOAT)
        while self._check(TokenType.MINUS):
            self._advance()  # consume -
            segment = ""
            tok = self._current()
            if tok.type == TokenType.IDENTIFIER:
                segment = self._advance().value
            elif tok.type == TokenType.INTEGER:
                segment = self._advance().value
                # Handle cases like "4o" where INTEGER is followed by IDENTIFIER
                if self._check(TokenType.IDENTIFIER):
                    segment += self._advance().value
            elif tok.type == TokenType.FLOAT:
                segment = self._advance().value
            else:
                break
            parts.append(segment)
        return '-'.join(parts)
