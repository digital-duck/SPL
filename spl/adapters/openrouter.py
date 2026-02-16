"""OpenRouter.ai adapter: unified production LLM provider.

Provides access to 100+ models (Claude, GPT, Gemini, Llama, Mistral, etc.)
through a single API endpoint and API key.
"""

from __future__ import annotations
import json
import os
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

# httpx is an optional dependency for this adapter
try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterAdapter(LLMAdapter):
    """LLM adapter using OpenRouter.ai as unified provider.

    Supports 100+ models through a single API:
    - Claude (anthropic/claude-sonnet-4-5)
    - GPT (openai/gpt-4o)
    - Gemini (google/gemini-2.0-flash)
    - Llama (meta-llama/llama-3.1-70b)
    - etc.

    Usage:
        adapter = OpenRouterAdapter(api_key="sk-or-...")
        result = await adapter.generate("Hello", model="anthropic/claude-sonnet-4-5")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENROUTER_API_URL,
        default_model: str = "anthropic/claude-sonnet-4-5",
        timeout: int = 180,
    ):
        if httpx is None:
            raise ImportError("httpx is required for OpenRouter adapter: pip install httpx")

        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var "
                "or pass api_key parameter."
            )
        self.base_url = base_url
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
        """Generate response via OpenRouter API."""
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
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/digital-duck/SPL",
            "X-Title": "SPL Engine",
        }

        response = await self._client.post(
            self.base_url,
            json=payload,
            headers=headers,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter API error ({response.status_code}): {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError:
            # Some models (e.g. z-ai/glm-4.6) return responses that embed raw
            # control characters inside JSON string values — Python's json parser
            # rejects these.  Strip ASCII control chars (except \t \n \r) and
            # retry once before giving up.
            import re as _re
            sanitized = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", response.text)
            try:
                data = json.loads(sanitized)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"OpenRouter API returned unparseable JSON "
                    f"(model={model}): {exc}"
                ) from exc

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
            cost_usd=None,  # OpenRouter returns cost separately
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using model-aware estimation."""
        counter = TokenCounter(model or self.default_model)
        return counter.count(text)

    def list_models(self) -> list[str]:
        """Return commonly used OpenRouter models."""
        return [
            "anthropic/claude-opus-4-6",
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-haiku-4-5",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-2.0-flash",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mistral-large",
        ]

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
