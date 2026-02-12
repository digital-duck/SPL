"""Abstract base class for LLM adapters."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class GenerationResult:
    """Result from an LLM generation call."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float | None = None


class LLMAdapter(ABC):
    """Abstract interface for LLM providers.

    All SPL LLM backends must implement this interface.
    Concrete implementations: OpenRouterAdapter (production), ClaudeCLIAdapter (dev).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt/message.
            model: Model identifier (e.g., 'claude-sonnet-4-5', 'gpt-4o').
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature (0.0 - 2.0).
            system: Optional system prompt.

        Returns:
            GenerationResult with content and usage metadata.
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens in text for the given model.

        Args:
            text: Input text.
            model: Model name for model-specific tokenization.

        Returns:
            Estimated token count.
        """
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this adapter."""
        ...

    def _measure_time(self):
        """Return a context-manager-like start time for latency measurement."""
        return time.perf_counter()

    def _elapsed_ms(self, start: float) -> float:
        """Calculate elapsed milliseconds."""
        return (time.perf_counter() - start) * 1000
