"""Model-aware token counting for SPL budget management."""

from __future__ import annotations


# Model family to approximate chars-per-token ratio
_MODEL_CPT: dict[str, float] = {
    "claude": 3.5,
    "gpt": 4.0,
    "gemini": 3.8,
    "llama": 3.5,
    "mistral": 3.5,
}

# Try to import tiktoken for accurate OpenAI model counting
_tiktoken = None
try:
    import tiktoken as _tiktoken
except ImportError:
    pass


class TokenCounter:
    """Count tokens for text given a model name."""

    def __init__(self, model: str | None = None):
        self.model = model or "claude"
        self._encoder = None
        if _tiktoken and self._is_openai_model():
            try:
                self._encoder = _tiktoken.encoding_for_model(self.model)
            except KeyError:
                self._encoder = _tiktoken.get_encoding("cl100k_base")

    def _is_openai_model(self) -> bool:
        lower = self.model.lower()
        return any(prefix in lower for prefix in ("gpt", "o1", "o3", "text-embedding"))

    def count(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        if self._encoder:
            return len(self._encoder.encode(text))
        # Estimate based on model family
        cpt = self._get_chars_per_token()
        return max(1, int(len(text) / cpt))

    def _get_chars_per_token(self) -> float:
        lower = self.model.lower()
        for family, cpt in _MODEL_CPT.items():
            if family in lower:
                return cpt
        return 4.0  # default estimate

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within a token budget."""
        current = self.count(text)
        if current <= max_tokens:
            return text
        # Estimate character position
        ratio = max_tokens / max(current, 1)
        char_limit = int(len(text) * ratio * 0.95)  # slight safety margin
        truncated = text[:char_limit]
        # Trim to last complete sentence if possible
        for sep in ('.', '\n', ' '):
            last = truncated.rfind(sep)
            if last > char_limit * 0.8:
                truncated = truncated[:last + 1]
                break
        return truncated

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float | None:
        """Estimate USD cost based on model pricing (approximate)."""
        pricing = {
            "claude-opus": (15.0, 75.0),
            "claude-sonnet": (3.0, 15.0),
            "claude-haiku": (0.25, 1.25),
            "gpt-4o": (2.5, 10.0),
            "gpt-4": (30.0, 60.0),
            "gpt-3.5": (0.5, 1.5),
        }
        lower = self.model.lower()
        for model_prefix, (inp_price, out_price) in pricing.items():
            if model_prefix in lower:
                cost = (input_tokens / 1_000_000 * inp_price +
                        output_tokens / 1_000_000 * out_price)
                return round(cost, 6)
        return None
