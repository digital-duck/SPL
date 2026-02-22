"""Cloud Direct adapter: direct API access to major LLM providers.

Provides direct access to cloud providers without intermediaries:
- Anthropic Claude API
- Google Gemini API
- OpenAI GPT API

Each provider uses their native API endpoints for optimal performance and pricing.
"""

from __future__ import annotations
import json
import logging
import os
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

_log = logging.getLogger(__name__)

# httpx is an optional dependency for this adapter
try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


# API endpoints
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class CloudDirectAdapter(LLMAdapter):
    """LLM adapter using direct cloud provider APIs.

    Supports direct access to:
    - Anthropic Claude (claude-opus-4.6, claude-sonnet-4.6, claude-haiku-4.5)
    - Google Gemini (gemini-2.5-pro, gemini-2.5-flash)
    - OpenAI GPT (gpt-5.2, gpt-4o, gpt-4o-mini)

    Usage:
        adapter = CloudDirectAdapter()
        result = await adapter.generate("Hello", model="claude-opus-4.6")
    """

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        google_api_key: str | None = None,
        openai_api_key: str | None = None,
        timeout: int = 180,
    ):
        if httpx is None:
            raise ImportError("httpx is required for CloudDirect adapter: pip install httpx")

        # Initialize API keys from env or params
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")

        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    def _get_provider_from_model(self, model: str) -> str:
        """Determine provider from model name."""
        if model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gemini-"):
            return "google"
        elif model.startswith("gpt-"):
            return "openai"
        else:
            raise ValueError(f"Unsupported model: {model}")

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate response via direct cloud provider APIs."""
        start = self._measure_time()

        if not model:
            model = "claude-sonnet-4.6"  # Default model

        provider = self._get_provider_from_model(model)

        if provider == "anthropic":
            return await self._generate_anthropic(prompt, model, max_tokens, temperature, system, start)
        elif provider == "google":
            return await self._generate_google(prompt, model, max_tokens, temperature, system, start)
        elif provider == "openai":
            return await self._generate_openai(prompt, model, max_tokens, temperature, system, start)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _generate_anthropic(
        self, prompt: str, model: str, max_tokens: int, temperature: float,
        system: str | None, start: float
    ) -> GenerationResult:
        """Generate using Anthropic Claude API."""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required for Claude models")

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            payload["system"] = system

        headers = {
            "x-api-key": self.anthropic_api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        response = await self._client.post(
            ANTHROPIC_API_URL,
            json=payload,
            headers=headers,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Anthropic API error ({response.status_code}): {response.text}")

        data = response.json()
        content = data["content"][0]["text"]
        usage = data.get("usage", {})

        latency = self._elapsed_ms(start)
        input_tokens = usage.get("input_tokens", self.count_tokens(prompt, model))
        output_tokens = usage.get("output_tokens", self.count_tokens(content, model))

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=None,
        )

    async def _generate_google(
        self, prompt: str, model: str, max_tokens: int, temperature: float,
        system: str | None, start: float
    ) -> GenerationResult:
        """Generate using Google Gemini API."""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY required for Gemini models")

        # Construct the full URL with model and API key
        url = f"{GOOGLE_API_URL}/{model}:generateContent?key={self.google_api_key}"

        contents = []
        if system:
            contents.append({"parts": [{"text": system}], "role": "user"})
        contents.append({"parts": [{"text": prompt}], "role": "user"})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        headers = {"Content-Type": "application/json"}

        response = await self._client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"Google API error ({response.status_code}): {response.text}")

        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})

        latency = self._elapsed_ms(start)
        input_tokens = usage.get("promptTokenCount", self.count_tokens(prompt, model))
        output_tokens = usage.get("candidatesTokenCount", self.count_tokens(content, model))

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=None,
        )

    async def _generate_openai(
        self, prompt: str, model: str, max_tokens: int, temperature: float,
        system: str | None, start: float
    ) -> GenerationResult:
        """Generate using OpenAI GPT API."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for GPT models")

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
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        response = await self._client.post(
            OPENAI_API_URL,
            json=payload,
            headers=headers,
        )

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API error ({response.status_code}): {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
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
            cost_usd=None,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using model-aware estimation."""
        counter = TokenCounter(model or "claude-sonnet-4.6")
        return counter.count(text)

    def list_models(self) -> list[str]:
        """Return available models for cloud direct access."""
        return [
            # Anthropic
            "claude-opus-4.6",
            "claude-sonnet-4.6",
            "claude-haiku-4.5",
            # Google
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            # OpenAI
            "gpt-5.2",
            "gpt-4o",
            "gpt-4o-mini",
        ]

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()