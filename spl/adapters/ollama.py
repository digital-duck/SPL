"""Ollama adapter: local open-source LLM provider.

Runs models locally via Ollama (https://ollama.ai).
No API key required — cost is always $0.00.

Requires Ollama to be running: https://ollama.ai/download
Pull a model first: ollama pull llama3.2

Ollama exposes an OpenAI-compatible endpoint at http://localhost:11434/v1,
so the implementation closely mirrors the OpenRouter adapter.
"""

from __future__ import annotations
import os
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaAdapter(LLMAdapter):
    """LLM adapter for locally-running Ollama models.

    Zero cost — all inference runs on your own hardware.
    Supports any model installed via `ollama pull <model>`.

    Popular models:
        ollama pull llama3.2          # Meta Llama 3.2 3B (fast, lightweight)
        ollama pull llama3.1:8b       # Meta Llama 3.1 8B
        ollama pull mistral           # Mistral 7B
        ollama pull qwen2.5-coder     # Qwen 2.5 Coder 7B
        ollama pull codellama         # Code Llama
        ollama pull phi3              # Microsoft Phi-3 Mini
        ollama pull gemma2            # Google Gemma 2 9B

    Usage:
        adapter = OllamaAdapter()
        result = await adapter.generate("Hello", model="llama3.2")

        # Custom host (remote Ollama server):
        adapter = OllamaAdapter(base_url="http://192.168.1.10:11434")
    """

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "llama3.2",
        timeout: int = 120,
    ):
        if httpx is None:
            raise ImportError("httpx is required for Ollama adapter: pip install httpx")

        self.base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)
        ).rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate response via Ollama's OpenAI-compatible chat endpoint."""
        start = self._measure_time()
        model = model or self.default_model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        url = f"{self.base_url}/v1/chat/completions"

        try:
            response = await self._client.post(url, json=payload)
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama error ({response.status_code}): {response.text}"
            )

        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        latency = self._elapsed_ms(start)
        input_tokens = usage.get("prompt_tokens", self.count_tokens(prompt, model))
        output_tokens = usage.get("completion_tokens", self.count_tokens(content, model))

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=0.0,  # local inference, always free
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Estimate token count for Ollama models.

        Ollama hosts a variety of model families (Llama, Mistral, Qwen, etc.)
        that use different tokenizers. We use character-based estimation as a
        safe universal fallback (~4 chars per token).
        """
        counter = TokenCounter(model or self.default_model)
        return counter.count(text)

    def list_models(self) -> list[str]:
        """Return models currently installed in the local Ollama instance.

        Falls back to a curated default list if Ollama is not reachable.
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

        # Ollama not reachable — return popular models as reference
        return [
            "llama3.2",
            "llama3.1:8b",
            "mistral",
            "qwen2.5-coder",
            "codellama",
            "phi3",
            "gemma2",
            "deepseek-r1:7b",
        ]

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
