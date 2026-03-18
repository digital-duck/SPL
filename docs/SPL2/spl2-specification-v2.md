# SPL 2.0 Language Specification v1.0
## Extension of SPL 1.0 for Agentic Workflow Orchestration

---

## Executive Summary

This specification defines **SPL 2.0**, which extends **SPL 1.0** with primitives for agentic workflow orchestration. The design principle is **backward compatibility**: all SPL 1.0 programs remain valid in SPL 2.0, and new constructs are purely additive.

### What SPL 1.0 Already Provides

| Feature | Syntax |
|---------|--------|
| Prompt Definition | `PROMPT name WITH BUDGET n tokens USING MODEL model` |
| Context Selection | `SELECT item AS alias LIMIT n tokens` |
| LLM Generation | `GENERATE function(args) WITH OUTPUT BUDGET n tokens` |
| Conditions | `WHERE condition` |
| CTEs | `WITH name AS (...)` |
| Storage | `STORE RESULT IN memory.key` |
| Functions | `CREATE FUNCTION name(...) RETURNS type AS $$ body $$` |
| Execution | `EXPLAIN PROMPT`, `EXECUTE PROMPT` |

### What SPL 2.0 Adds

| Feature | Syntax | Purpose |
|---------|--------|---------|
| **EVALUATE** | `EVALUATE expr WHEN condition THEN action END` | LLM-based condition evaluation |
| **WHILE** | `WHILE condition DO statements END` | Iteration with semantic termination |
| **DO Block** | `DO statements END` | Scope and error containment |
| **EXCEPTION** | `EXCEPTION WHEN type THEN action END` | LLM-specific error handling |
| **WORKFLOW** | `WORKFLOW name INPUT ... OUTPUT ... DO ... END` | Reusable workflow definitions |
| **COMMIT** | `COMMIT expr WITH status='...'` | Explicit output finalization |
| **RETRY** | `RETRY WITH fallback` | Recovery actions |
| **ASSIGNMENT** | `@var := expr` | Mutable state |

---

## Part 1: Grammar Extension (EBNF Delta)

### 1.1 New Keywords (Add to SPL 1.0)

```ebnf
(* New keywords for SPL 2.0 *)
new_keyword = 'EVALUATE' | 'WHEN' | 'THEN' | 'WHILE' | 'DO' | 'END'
            | 'EXCEPTION' | 'WORKFLOW' | 'INPUT' | 'OUTPUT' | 'COMMIT'
            | 'RETRY' | 'RAISE' | 'OTHERWISE' | 'PROCEDURE'
            | 'SECURITY' | 'ACCOUNTING' | 'CLASSIFICATION'
            | 'HALLUCINATION' | 'REFUSAL' | 'OVERFLOW' ;
```

### 1.2 New Token Types (Add to tokens.py)

```python
# New token types for SPL 2.0
EVALUATE = auto()
WHEN = auto()
THEN = auto()
WHILE = auto()
DO = auto()
END = auto()
EXCEPTION = auto()
WORKFLOW = auto()
INPUT = auto()
OUTPUT = auto()
COMMIT = auto()
RETRY = auto()
RAISE = auto()
OTHERWISE = auto()
PROCEDURE = auto()
SECURITY = auto()
ACCOUNTING = auto()
CLASSIFICATION = auto()
ASSIGN = auto()      # :=
COLON = auto()       # :

# Exception type keywords
HALLUCINATION = auto()
REFUSAL = auto()
OVERFLOW = auto()
ITERATIONS = auto()
BUDGET_EXCEEDED = auto()
```

### 1.3 Extended Statement Grammar

```ebnf
(* SPL 2.0 extends the statement production *)
statement        = prompt_stmt              -- SPL 1.0
                 | create_func_stmt         -- SPL 1.0
                 | explain_stmt             -- SPL 1.0
                 | execute_stmt             -- SPL 1.0
                 | workflow_stmt            -- SPL 2.0 NEW
                 | procedure_stmt           -- SPL 2.0 NEW
                 | evaluate_stmt            -- SPL 2.0 NEW
                 | while_stmt               -- SPL 2.0 NEW
                 | do_block                 -- SPL 2.0 NEW
                 | commit_stmt              -- SPL 2.0 NEW
                 | retry_stmt               -- SPL 2.0 NEW
                 | raise_stmt               -- SPL 2.0 NEW
                 | assignment_stmt ;        -- SPL 2.0 NEW
```

### 1.4 WORKFLOW Statement (New)

```ebnf
(* WORKFLOW - Top-level reusable workflow definition *)
workflow_stmt    = 'WORKFLOW' identifier
                   input_clause?
                   output_clause?
                   metadata_block?
                   do_block ;

input_clause     = 'INPUT' param_list ;
output_clause    = 'OUTPUT' param_list ;

param_list       = param (',' param)* ;
param            = variable type? ('DEFAULT' literal)? ;
```

### 1.5 PROCEDURE Statement (New)

```ebnf
(* PROCEDURE - Reusable workflow procedure *)
procedure_stmt   = 'PROCEDURE' identifier
                   '(' param_list? ')'
                   ('RETURNS' type)?
                   metadata_block?
                   do_block ;
```

### 1.6 DO Block (New)

```ebnf
(* DO Block - Scope and error containment *)
do_block         = 'DO' statement* 'END'
                 | 'DO' statement* exception_block ;

exception_block  = 'EXCEPTION' handler+ 'END' ;
handler          = 'WHEN' exception_pattern 'THEN' statement+ ;
exception_pattern = identifier               -- specific exception
                  | 'OTHERS' ;               -- catch-all
```

### 1.7 EVALUATE Statement (New)

```ebnf
(* EVALUATE - LLM-based or deterministic condition evaluation *)
evaluate_stmt    = 'EVALUATE' expression
                   when_clause+
                   otherwise_clause?
                   'END' ;

when_clause      = 'WHEN' condition 'THEN' statement+ ;
otherwise_clause = 'OTHERWISE' statement+ ;

(* Extended condition to include semantic evaluation *)
condition        = comparison_condition      -- existing
                 | semantic_condition        -- NEW
                 | compound_condition ;      -- existing

semantic_condition = string_literal ;  -- e.g., 'coherent', 'complete'
```

### 1.8 WHILE Statement (New)

```ebnf
(* WHILE - Iteration with optional semantic termination *)
while_stmt       = 'WHILE' condition 'DO' statement+ 'END' ;
```

### 1.9 COMMIT Statement (New)

```ebnf
(* COMMIT - Explicit output finalization *)
commit_stmt      = 'COMMIT' expression
                   ('WITH' commit_option (',' commit_option)*)? ;

commit_option    = 'STATUS' '=' string_literal
                 | identifier '=' expression ;
```

### 1.10 RETRY Statement (New)

```ebnf
(* RETRY - Recovery action *)
retry_stmt       = 'RETRY' ('WITH' with_clause)? ;
```

### 1.11 RAISE Statement (New)

```ebnf
(* RAISE - Explicit exception raising *)
raise_stmt       = 'RAISE' identifier (string_literal)? ;
```

### 1.12 Assignment Statement (New)

```ebnf
(* Assignment - Mutable state *)
assignment_stmt  = variable ':=' expression ;
```

### 1.13 Metadata Blocks (New)

```ebnf
(* Metadata blocks for workflows and procedures *)
metadata_block   = security_block
                 | accounting_block
                 | labels_block ;

security_block   = 'SECURITY' ':'
                   security_option+ ;

security_option  = 'CLASSIFICATION' ':' classification_level
                 | 'ENCRYPTION' ':' encryption_spec
                 | 'NODE_POLICY' ':' node_policy_spec ;

classification_level = 'public' | 'internal' | 'confidential' | 'restricted' ;

accounting_block = 'ACCOUNTING' ':'
                   accounting_option+ ;

accounting_option = 'BILLABLE_TO' ':' string_literal
                  | 'BUDGET_LIMIT' ':' number_literal 'moma_points'
                  | 'ALERT_AT' ':' number_literal '%' ;

labels_block     = 'LABELS' ':'
                   '{' label_entry (',' label_entry)* '}' ;

label_entry      = string_literal ':' string_literal ;
```

---

## Part 2: AST Node Extensions (Python)

### 2.1 New AST Nodes (Add to ast_nodes.py)

```python
# === SPL 2.0 New Nodes ===

@dataclass
class WorkflowStatement:
    """WORKFLOW <name> INPUT ... OUTPUT ... DO ... END"""
    name: str
    inputs: list[Parameter] = field(default_factory=list)
    outputs: list[Parameter] = field(default_factory=list)
    security: dict | None = None
    accounting: dict | None = None
    labels: dict | None = None
    body: list[Statement] = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


@dataclass
class ProcedureStatement:
    """PROCEDURE <name>(...) RETURNS type DO ... END"""
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    security: dict | None = None
    accounting: dict | None = None
    body: list[Statement] = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


@dataclass
class DoBlock:
    """DO <statements> END or DO <statements> EXCEPTION ... END"""
    statements: list[Statement] = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


@dataclass
class ExceptionHandler:
    """WHEN <exception_type> THEN <statements>"""
    exception_type: str  # e.g., "HallucinationDetected", "OTHERS"
    statements: list[Statement] = field(default_factory=list)


@dataclass
class EvaluateStatement:
    """EVALUATE <expr> WHEN <condition> THEN <statements> ... END"""
    expression: Expression
    when_clauses: list[WhenClause] = field(default_factory=list)
    otherwise_statements: list[Statement] = field(default_factory=list)


@dataclass
class WhenClause:
    """WHEN <condition> THEN <statements>"""
    condition: Condition  # Can be SemanticCondition or ComparisonCondition
    statements: list[Statement] = field(default_factory=list)


@dataclass
class SemanticCondition(Condition):
    """Semantic condition evaluated by LLM, e.g., 'coherent', 'complete'"""
    semantic_value: str  # The semantic condition string


@dataclass
class WhileStatement:
    """WHILE <condition> DO <statements> END"""
    condition: Condition
    body: list[Statement] = field(default_factory=list)


@dataclass
class CommitStatement:
    """COMMIT <expr> WITH status='...'"""
    expression: Expression
    options: dict = field(default_factory=dict)


@dataclass
class RetryStatement:
    """RETRY WITH fallback options"""
    fallback_options: dict = field(default_factory=dict)


@dataclass
class RaiseStatement:
    """RAISE <exception_type> [message]"""
    exception_type: str
    message: str | None = None


@dataclass
class AssignmentStatement:
    """@var := expr"""
    variable: str
    expression: Expression
```

### 2.2 Updated Program Node

```python
@dataclass
class Program:
    """Top-level program node containing a list of statements."""
    statements: list[
        PromptStatement | 
        CreateFunctionStatement | 
        ExplainStatement | 
        ExecuteStatement |
        WorkflowStatement |      # NEW
        ProcedureStatement       # NEW
    ] = field(default_factory=list)
```

---

## Part 3: Lexer Extensions

### 3.1 New Keywords (Add to KEYWORDS dict)

```python
# Add to KEYWORDS dict in tokens.py
KEYWORDS.update({
    "evaluate": TokenType.EVALUATE,
    "when": TokenType.WHEN,
    "then": TokenType.THEN,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "end": TokenType.END,
    "exception": TokenType.EXCEPTION,
    "workflow": TokenType.WORKFLOW,
    "input": TokenType.INPUT,
    "output": TokenType.OUTPUT,
    "commit": TokenType.COMMIT,
    "retry": TokenType.RETRY,
    "raise": TokenType.RAISE,
    "otherwise": TokenType.OTHERWISE,
    "procedure": TokenType.PROCEDURE,
    "security": TokenType.SECURITY,
    "accounting": TokenType.ACCOUNTING,
    "classification": TokenType.CLASSIFICATION,
    "hallucination": TokenType.HALLUCINATION,
    "refusal": TokenType.REFUSAL,
    "overflow": TokenType.OVERFLOW,
    "iterations": TokenType.ITERATIONS,
})
```

### 3.2 New Token Recognition (Add to Lexer)

```python
# In lexer.py, add recognition for := operator
# In tokenize() method, add:
elif ch == ':':
    if self._peek(1) == '=':
        self._emit(TokenType.ASSIGN, ':=')
        self._advance()
        self._advance()
    else:
        self._emit(TokenType.COLON, ':')
        self._advance()
```

---

## Part 4: Parser Extensions

### 4.1 Statement Dispatch Update

```python
def _parse_statement(self):
    # Existing SPL 1.0
    if self._check(TokenType.PROMPT) or self._check(TokenType.WITH):
        return self._parse_prompt_statement()
    elif self._check(TokenType.CREATE):
        return self._parse_create_function()
    elif self._check(TokenType.EXPLAIN):
        return self._parse_explain()
    elif self._check(TokenType.EXECUTE):
        return self._parse_execute()
    
    # SPL 2.0 New statements
    elif self._check(TokenType.WORKFLOW):
        return self._parse_workflow_statement()
    elif self._check(TokenType.PROCEDURE):
        return self._parse_procedure_statement()
    elif self._check(TokenType.EVALUATE):
        return self._parse_evaluate_statement()
    elif self._check(TokenType.WHILE):
        return self._parse_while_statement()
    elif self._check(TokenType.DO):
        return self._parse_do_block()
    elif self._check(TokenType.COMMIT):
        return self._parse_commit_statement()
    elif self._check(TokenType.RETRY):
        return self._parse_retry_statement()
    elif self._check(TokenType.RAISE):
        return self._parse_raise_statement()
    elif self._check(TokenType.AT):
        return self._parse_assignment_statement()
    
    else:
        raise ParseError(
            f"Expected statement keyword, got {self._current().type.name}",
            self._current()
        )
```

### 4.2 New Parser Methods

```python
def _parse_workflow_statement(self) -> WorkflowStatement:
    """Parse WORKFLOW name INPUT ... OUTPUT ... DO ... END"""
    self._expect(TokenType.WORKFLOW)
    name = self._expect(TokenType.IDENTIFIER).value
    
    inputs = []
    if self._check(TokenType.INPUT):
        self._advance()
        inputs = self._parse_param_list()
    
    outputs = []
    if self._check(TokenType.OUTPUT):
        self._advance()
        outputs = self._parse_param_list()
    
    security = None
    if self._check(TokenType.SECURITY):
        security = self._parse_security_block()
    
    accounting = None
    if self._check(TokenType.ACCOUNTING):
        accounting = self._parse_accounting_block()
    
    do_block = self._parse_do_block()
    
    return WorkflowStatement(
        name=name,
        inputs=inputs,
        outputs=outputs,
        security=security,
        accounting=accounting,
        body=do_block.statements,
        exception_handlers=do_block.exception_handlers
    )


def _parse_do_block(self) -> DoBlock:
    """Parse DO statements [EXCEPTION handlers] END"""
    self._expect(TokenType.DO)
    
    statements = []
    while not self._check(TokenType.END) and not self._check(TokenType.EXCEPTION):
        statements.append(self._parse_statement())
    
    exception_handlers = []
    if self._check(TokenType.EXCEPTION):
        exception_handlers = self._parse_exception_block()
    
    self._expect(TokenType.END)
    
    return DoBlock(statements=statements, exception_handlers=exception_handlers)


def _parse_exception_block(self) -> list[ExceptionHandler]:
    """Parse EXCEPTION WHEN type THEN statements ... END"""
    self._expect(TokenType.EXCEPTION)
    
    handlers = []
    while self._check(TokenType.WHEN):
        self._advance()  # WHEN
        exception_type = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.THEN)
        
        handler_statements = []
        while not self._check(TokenType.WHEN) and not self._check(TokenType.END):
            handler_statements.append(self._parse_statement())
        
        handlers.append(ExceptionHandler(
            exception_type=exception_type,
            statements=handler_statements
        ))
    
    self._expect(TokenType.END)
    return handlers


def _parse_evaluate_statement(self) -> EvaluateStatement:
    """Parse EVALUATE expr WHEN condition THEN statements ... END"""
    self._expect(TokenType.EVALUATE)
    expression = self._parse_expression()
    
    when_clauses = []
    while self._check(TokenType.WHEN):
        self._advance()  # WHEN
        condition = self._parse_condition()  # Extended to handle semantic conditions
        self._expect(TokenType.THEN)
        
        then_statements = []
        while not self._check(TokenType.WHEN) and not self._check(TokenType.OTHERWISE) and not self._check(TokenType.END):
            then_statements.append(self._parse_statement())
        
        when_clauses.append(WhenClause(
            condition=condition,
            statements=then_statements
        ))
    
    otherwise_statements = []
    if self._check(TokenType.OTHERWISE):
        self._advance()
        while not self._check(TokenType.END):
            otherwise_statements.append(self._parse_statement())
    
    self._expect(TokenType.END)
    
    return EvaluateStatement(
        expression=expression,
        when_clauses=when_clauses,
        otherwise_statements=otherwise_statements
    )


def _parse_while_statement(self) -> WhileStatement:
    """Parse WHILE condition DO statements END"""
    self._expect(TokenType.WHILE)
    condition = self._parse_condition()
    self._expect(TokenType.DO)
    
    statements = []
    while not self._check(TokenType.END):
        statements.append(self._parse_statement())
    
    self._expect(TokenType.END)
    
    return WhileStatement(condition=condition, body=statements)


def _parse_condition(self) -> Condition:
    """Extended condition parsing to handle semantic conditions"""
    # Check if this is a semantic condition (string literal)
    if self._check(TokenType.STRING):
        semantic_value = self._advance().value
        return SemanticCondition(semantic_value=semantic_value)
    
    # Otherwise, use existing comparison condition logic
    return self._parse_comparison_condition()


def _parse_commit_statement(self) -> CommitStatement:
    """Parse COMMIT expr WITH options"""
    self._expect(TokenType.COMMIT)
    expression = self._parse_expression()
    
    options = {}
    if self._check(TokenType.WITH):
        self._advance()
        while True:
            key = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.EQ)
            value = self._parse_expression()
            options[key] = value
            
            if not self._check(TokenType.COMMA):
                break
            self._advance()
    
    return CommitStatement(expression=expression, options=options)


def _parse_assignment_statement(self) -> AssignmentStatement:
    """Parse @var := expr"""
    self._expect(TokenType.AT)
    var_name = self._expect(TokenType.IDENTIFIER).value
    self._expect(TokenType.ASSIGN)
    expression = self._parse_expression()
    
    return AssignmentStatement(variable=var_name, expression=expression)
```

---

## Part 5: Semantic Analysis Extensions

### 5.1 Condition Type Inference

```python
def infer_condition_type(condition: Condition) -> str:
    """
    Determine if a condition is deterministic or semantic.
    
    Returns:
        'deterministic' - Can be evaluated without LLM
        'semantic' - Requires LLM to evaluate
        'hybrid' - Mix of both
    """
    if isinstance(condition, SemanticCondition):
        return 'semantic'
    
    if isinstance(condition, Condition):
        # Check if left or right side is a number/boolean comparison
        left_type = infer_expression_type(condition.left)
        right_type = infer_expression_type(condition.right)
        
        if left_type in ('number', 'boolean') and right_type in ('number', 'boolean'):
            return 'deterministic'
        
        if left_type == 'text' or right_type == 'text':
            # Text comparison might need LLM
            if condition.operator in ('=', '!='):
                return 'semantic'  # String equality might need semantic comparison
        
        return 'deterministic'  # Default for known comparisons
    
    return 'semantic'  # Unknown condition type
```

### 5.2 Exception Type Validation

```python
VALID_EXCEPTION_TYPES = {
    'HallucinationDetected',
    'RefusalToAnswer',
    'ContextLengthExceeded',
    'ModelOverloaded',
    'QualityBelowThreshold',
    'MaxIterationsReached',
    'BudgetExceeded',
    'NodeUnavailable',
    'OTHERS'
}

def validate_exception_type(exception_type: str) -> bool:
    """Validate that exception type is recognized."""
    return exception_type in VALID_EXCEPTION_TYPES
```

---

## Part 6: Examples

### 6.1 Simple EVALUATE (Backward Compatible with SPL 1.0)

```
-- SPL 1.0 style (still works)
PROMPT analyze
WITH BUDGET 4000 tokens
USING MODEL claude-sonnet-4-5

SELECT
    context.document AS doc LIMIT 2000 tokens

GENERATE
    analysis(doc)
WITH OUTPUT BUDGET 1500 tokens;
```

### 6.2 EVALUATE with Deterministic Condition

```
-- SPL 2.0 adds EVALUATE
PROMPT analyze_with_quality_check
WITH BUDGET 8000 tokens
USING MODEL claude-sonnet-4-5

SELECT
    context.document AS doc LIMIT 2000 tokens

GENERATE
    analysis(doc) WITH OUTPUT BUDGET 1500 tokens
INTO @result

GENERATE
    quality_score(@result) WITH OUTPUT BUDGET 100 tokens
INTO @score

EVALUATE @score
  WHEN > 0.8 THEN
    COMMIT @result
  WHEN <= 0.8 THEN
    GENERATE improved_analysis(doc, @result)
    COMMIT @improved_analysis WITH status='refined'
END;
```

### 6.3 EVALUATE with Semantic Condition

```
-- Semantic evaluation using LLM as judge
PROMPT summarize_with_validation
WITH BUDGET 10000 tokens
USING MODEL claude-sonnet-4-5

SELECT
    context.article AS article LIMIT 5000 tokens

GENERATE
    summary(article) WITH OUTPUT BUDGET 500 tokens
INTO @summary

EVALUATE @summary
  WHEN 'coherent' THEN
    COMMIT @summary
  WHEN 'hallucination' THEN
    RETRY WITH temperature=0.1
  WHEN 'incomplete' THEN
    GENERATE extended_summary(article, @summary)
    COMMIT @extended_summary
END;
```

### 6.4 WHILE Loop with Semantic Termination

```
WORKFLOW iterative_refinement
  INPUT: @task text
  OUTPUT: @result text
DO
  @iteration := 0
  @max_iterations := 5
  
  GENERATE draft(@task) INTO @current
  
  WHILE @iteration < @max_iterations AND NOT EVALUATE 'complete' FROM @current DO
    GENERATE critique(@current) INTO @feedback
    GENERATE refined(@current, @feedback) INTO @current
    @iteration := @iteration + 1
  END
  
  COMMIT @current WITH iterations=@iteration

EXCEPTION
  WHEN MaxIterationsReached THEN
    COMMIT @current WITH status='partial'
END
```

### 6.5 Full ReAct Pattern

```
WORKFLOW react_agent
  INPUT: @task text
  OUTPUT: @answer text
DO
  @iteration := 0
  @history := ''
  @context := ''
  
  WHILE @iteration < 10 AND NOT EVALUATE 'task_complete' FROM @task, @history DO
    
    -- Reasoning step
    GENERATE thought(@task, @history, @context) INTO @current_thought
    
    -- Action decision
    GENERATE action_decision(@current_thought) INTO @action, @action_input
    
    -- Execute action
    EVALUATE @action
      WHEN 'search' THEN
        SELECT results FROM rag.query(@action_input, top_k=5) INTO @observation
      WHEN 'calculate' THEN
        CALL calculator(@action_input) INTO @observation
      WHEN 'answer' THEN
        @answer := @action_input
        COMMIT @answer
    END
    
    @history := @history + '\nThought: ' + @current_thought + '\nAction: ' + @action + '\nObservation: ' + @observation
    @iteration := @iteration + 1
    
  END
  
EXCEPTION
  WHEN MaxIterationsReached THEN
    GENERATE best_answer(@history) INTO @answer
    COMMIT @answer WITH status='partial'
END
```

### 6.6 Exception Handling for LLM Failures

```
WORKFLOW safe_generation
  INPUT: @prompt text
  OUTPUT: @result text
DO
  GENERATE response(@prompt) INTO @result
  
EXCEPTION
  WHEN HallucinationDetected THEN
    GENERATE response(@prompt) WITH temperature=0.1, mode='conservative' INTO @result
    COMMIT @result WITH status='conservative'
  
  WHEN ContextLengthExceeded THEN
    SELECT compressed FROM context(@prompt) LIMIT 50% INTO @compressed
    RETRY WITH @compressed
  
  WHEN RefusalToAnswer THEN
    COMMIT 'Unable to generate response due to content policy' WITH status='refused'
  
  WHEN BudgetExceeded THEN
    COMMIT @partial_result WITH status='truncated'
END
```

---

## Part 7: Implementation Roadmap

### Phase 1: Lexer and Token Extensions (Week 1)
- [ ] Add new token types to `tokens.py`
- [ ] Add new keywords to `KEYWORDS` dict
- [ ] Add `:=` operator recognition in lexer
- [ ] Write lexer tests for new tokens

### Phase 2: AST Node Extensions (Week 1-2)
- [ ] Add new AST node classes to `ast_nodes.py`
- [ ] Ensure backward compatibility with existing nodes
- [ ] Write AST node tests

### Phase 3: Parser Extensions (Week 2-3)
- [ ] Add statement dispatch for new statement types
- [ ] Implement `_parse_workflow_statement`
- [ ] Implement `_parse_procedure_statement`
- [ ] Implement `_parse_do_block`
- [ ] Implement `_parse_evaluate_statement`
- [ ] Implement `_parse_while_statement`
- [ ] Implement `_parse_commit_statement`
- [ ] Implement `_parse_assignment_statement`
- [ ] Write parser tests for all new constructs

### Phase 4: Semantic Analyzer Extensions (Week 3-4)
- [ ] Add condition type inference
- [ ] Add exception type validation
- [ ] Add scope analysis for variables
- [ ] Write semantic analysis tests

### Phase 5: Executor Extensions (Week 4-6)
- [ ] Implement EVALUATE execution (deterministic vs semantic)
- [ ] Implement WHILE execution with iteration tracking
- [ ] Implement EXCEPTION handling
- [ ] Implement COMMIT output
- [ ] Implement RETRY logic
- [ ] Write executor tests

### Phase 6: Integration with Momagrid (Week 6-8)
- [ ] Define IR extensions for workflow constructs
- [ ] Hub integration for workflow coordination
- [ ] State management for iterative workflows
- [ ] Accounting integration for Moma Points

### Phase 7: Case Studies and Validation (Week 8-10)
- [ ] Implement ReAct procedure
- [ ] Implement Self-Refine procedure
- [ ] Implement Tree-of-Thought procedure
- [ ] Benchmark against LangGraph

---

## Part 8: Backward Compatibility Checklist

| SPL 1.0 Feature | SPL 2.0 Status |
|-----------------|----------------|
| `PROMPT` statement | ✅ Unchanged |
| `SELECT` clause | ✅ Unchanged |
| `GENERATE` clause | ✅ Unchanged, extended with `INTO` |
| `WHERE` clause | ✅ Unchanged |
| `WITH ... AS` CTE | ✅ Unchanged |
| `STORE RESULT IN` | ✅ Unchanged |
| `CREATE FUNCTION` | ✅ Unchanged |
| `EXPLAIN PROMPT` | ✅ Unchanged |
| `EXECUTE PROMPT` | ✅ Unchanged |
| `system_role()` | ✅ Unchanged |
| `context.field` | ✅ Unchanged |
| `rag.query()` | ✅ Unchanged |
| `memory.get()` | ✅ Unchanged |
| `LIMIT n tokens` | ✅ Unchanged |
| `WITH BUDGET n tokens` | ✅ Unchanged |
| `USING MODEL name` | ✅ Unchanged |

All SPL 1.0 programs should parse and execute identically in SPL 2.0.