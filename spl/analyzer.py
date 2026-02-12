"""SPL Semantic Analyzer: validates AST for correctness."""

from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement, ExplainStatement,
    ExecuteStatement, SelectItem, CTEClause, GenerateClause,
    SystemRoleCall, ContextRef, RagQuery, MemoryGet, Identifier,
    DottedName, FunctionCall,
)


class AnalysisError(Exception):
    """Raised when semantic analysis finds an error."""
    pass


class AnalysisWarning:
    """Non-fatal warning from analysis."""
    def __init__(self, message: str):
        self.message = message

    def __repr__(self) -> str:
        return f"Warning: {self.message}"


class AnalysisResult:
    """Result of semantic analysis."""
    def __init__(self, ast: Program):
        self.ast = ast
        self.warnings: list[AnalysisWarning] = []
        self.defined_prompts: dict[str, PromptStatement] = {}
        self.defined_functions: dict[str, CreateFunctionStatement] = {}

    @property
    def is_valid(self) -> bool:
        return True  # If we got here without raising, it's valid


class Analyzer:
    """Semantic analyzer for SPL AST."""

    def analyze(self, program: Program) -> AnalysisResult:
        """Validate the AST and return analysis result."""
        result = AnalysisResult(ast=program)

        for stmt in program.statements:
            if isinstance(stmt, CreateFunctionStatement):
                self._analyze_create_function(stmt, result)
            elif isinstance(stmt, PromptStatement):
                self._analyze_prompt(stmt, result)
            elif isinstance(stmt, ExplainStatement):
                self._analyze_explain(stmt, result)
            elif isinstance(stmt, ExecuteStatement):
                self._analyze_execute(stmt, result)

        return result

    def _analyze_create_function(self, stmt: CreateFunctionStatement, result: AnalysisResult):
        if stmt.name in result.defined_functions:
            raise AnalysisError(f"Function '{stmt.name}' already defined")
        result.defined_functions[stmt.name] = stmt

    def _analyze_prompt(self, stmt: PromptStatement, result: AnalysisResult):
        if stmt.name in result.defined_prompts:
            raise AnalysisError(f"Prompt '{stmt.name}' already defined")
        result.defined_prompts[stmt.name] = stmt

        # Collect all aliases defined in CTEs and SELECT
        defined_aliases: set[str] = set()

        for cte in stmt.ctes:
            if cte.name in defined_aliases:
                raise AnalysisError(f"Duplicate CTE name '{cte.name}'")
            defined_aliases.add(cte.name)
            self._validate_select_items(cte.select_items, defined_aliases, result)

        for item in stmt.select_items:
            if item.alias:
                defined_aliases.add(item.alias)

        # Validate budget arithmetic
        if stmt.budget is not None:
            total_limits = 0
            for item in stmt.select_items:
                if item.limit_tokens is not None:
                    total_limits += item.limit_tokens
            for cte in stmt.ctes:
                if cte.limit_tokens is not None:
                    total_limits += cte.limit_tokens

            output_budget = 0
            if stmt.generate_clause and stmt.generate_clause.output_budget:
                output_budget = stmt.generate_clause.output_budget

            if total_limits + output_budget > stmt.budget:
                result.warnings.append(AnalysisWarning(
                    f"Sum of LIMIT clauses ({total_limits}) + output budget ({output_budget}) "
                    f"= {total_limits + output_budget} exceeds total budget ({stmt.budget}). "
                    f"Optimizer will apply compression."
                ))

        # Validate GENERATE references
        if stmt.generate_clause:
            self._validate_generate(stmt.generate_clause, defined_aliases, result)

    def _validate_select_items(self, items: list[SelectItem], aliases: set[str],
                               result: AnalysisResult):
        for item in items:
            if item.limit_tokens is not None and item.limit_tokens <= 0:
                raise AnalysisError("LIMIT tokens must be positive")

    def _validate_generate(self, gen: GenerateClause, aliases: set[str],
                           result: AnalysisResult):
        # Check that GENERATE arguments reference defined aliases
        for arg in gen.arguments:
            if isinstance(arg, Identifier):
                if arg.name not in aliases:
                    result.warnings.append(AnalysisWarning(
                        f"GENERATE argument '{arg.name}' is not a defined alias. "
                        f"Available: {', '.join(sorted(aliases))}"
                    ))

        if gen.temperature is not None:
            if gen.temperature < 0 or gen.temperature > 2.0:
                raise AnalysisError(
                    f"Temperature must be between 0 and 2.0, got {gen.temperature}"
                )

        if gen.output_budget is not None and gen.output_budget <= 0:
            raise AnalysisError("OUTPUT BUDGET must be positive")

    def _analyze_explain(self, stmt: ExplainStatement, result: AnalysisResult):
        # EXPLAIN can reference prompts defined later, so just record for now
        pass

    def _analyze_execute(self, stmt: ExecuteStatement, result: AnalysisResult):
        # EXECUTE can reference prompts defined earlier
        pass
