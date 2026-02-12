"""SPL built-in and user-defined function registry."""

from __future__ import annotations
from spl.ast_nodes import CreateFunctionStatement


class FunctionRegistry:
    """Registry for SPL functions (both built-in and user-defined)."""

    def __init__(self):
        self._functions: dict[str, CreateFunctionStatement] = {}
        self._builtins: dict[str, callable] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in SPL functions."""
        self._builtins["summarize"] = self._builtin_summarize
        self._builtins["len"] = self._builtin_len
        self._builtins["upper"] = self._builtin_upper
        self._builtins["lower"] = self._builtin_lower
        self._builtins["truncate"] = self._builtin_truncate

    def register(self, func_stmt: CreateFunctionStatement):
        """Register a user-defined function."""
        self._functions[func_stmt.name] = func_stmt

    def get(self, name: str) -> CreateFunctionStatement | None:
        """Get a user-defined function by name."""
        return self._functions.get(name)

    def is_builtin(self, name: str) -> bool:
        """Check if a function name is a built-in."""
        return name.lower() in self._builtins

    def call_builtin(self, name: str, *args) -> str:
        """Call a built-in function."""
        func = self._builtins.get(name.lower())
        if func is None:
            raise ValueError(f"Unknown built-in function: {name}")
        return func(*args)

    def list_functions(self) -> dict[str, str]:
        """List all available functions with descriptions."""
        result = {}
        for name in self._builtins:
            result[name] = f"Built-in: {name}"
        for name, func in self._functions.items():
            result[name] = f"User-defined: {func.return_type}"
        return result

    # === Built-in Implementations ===

    @staticmethod
    def _builtin_summarize(text: str, max_tokens: int = 200) -> str:
        """Simple extractive summarization (first N sentences)."""
        if not text:
            return ""
        sentences = text.replace('\n', ' ').split('. ')
        result = []
        token_count = 0
        for sentence in sentences:
            est_tokens = len(sentence) // 4
            if token_count + est_tokens > max_tokens:
                break
            result.append(sentence)
            token_count += est_tokens
        return '. '.join(result)

    @staticmethod
    def _builtin_len(text: str) -> str:
        """Return estimated token count as string."""
        return str(len(text) // 4)

    @staticmethod
    def _builtin_upper(text: str) -> str:
        return text.upper()

    @staticmethod
    def _builtin_lower(text: str) -> str:
        return text.lower()

    @staticmethod
    def _builtin_truncate(text: str, max_chars: int = 1000) -> str:
        """Truncate text to max characters."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
