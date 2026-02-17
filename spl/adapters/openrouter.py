"""OpenRouter.ai adapter: unified production LLM provider.

Provides access to 100+ models (Claude, GPT, Gemini, Llama, Mistral, etc.)
through a single API endpoint and API key.
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

        _log.debug(
            "openrouter raw response  model=%s  status=%s  bytes=%d\n%s",
            model, response.status_code, len(response.text), response.text,
        )

        try:
            data = response.json()
        except json.JSONDecodeError as _first_exc:
            _log.warning(
                "openrouter JSON parse failed (pass 1)  model=%s  error=%s  "
                "raw_bytes=%d  — stripping control chars and retrying",
                model, _first_exc, len(response.text),
            )
            # Pass 1 — strip ASCII control chars (GLM-4.6 embeds raw control bytes)
            import re as _re
            sanitized = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", response.text)
            try:
                data = json.loads(sanitized)
            except json.JSONDecodeError as _second_exc:
                _log.error(
                    "openrouter JSON parse failed (pass 2)  model=%s  error=%s\n"
                    "=== RAW RESPONSE BODY (first 8000 chars) ===\n%s\n"
                    "=== END RAW RESPONSE ===",
                    model, _second_exc, response.text[:8000],
                )
                # Pass 2 — regex extraction (handles truncated responses, e.g. GLM-5)
                # OpenRouter always wraps content as: "content": "<escaped text>"
                # We capture the value even without the closing quote so truncated
                # responses are partially recoverable.
                m = _re.search(
                    r'"content"\s*:\s*"((?:[^"\\]|\\.)*)',
                    sanitized,
                    _re.DOTALL,
                )
                if not m:
                    _log.error(
                        "openrouter regex extraction also failed  model=%s  "
                        "full raw body saved below\n%s",
                        model, response.text,
                    )
                    raise RuntimeError(
                        f"OpenRouter API returned unparseable JSON "
                        f"(model={model}): could not locate content field"
                    )
                raw = m.group(1)
                # Unescape standard JSON escape sequences
                content_recovered = (
                    raw.replace("\\n", "\n")
                       .replace("\\t", "\t")
                       .replace('\\"', '"')
                       .replace("\\\\", "\\")
                       .replace("\\/", "/")
                )
                content_recovered += (
                    "\n\n[NOTE: Response was truncated — "
                    "JSON parse failed at the boundary. Content may be incomplete.]"
                )
                _log.warning(
                    "openrouter regex extraction recovered %d chars  model=%s",
                    len(content_recovered), model,
                )
                latency = self._elapsed_ms(start)
                tok_in  = self.count_tokens(prompt, model)
                tok_out = self.count_tokens(content_recovered, model)
                return GenerationResult(
                    content=content_recovered,
                    model=model,
                    input_tokens=tok_in,
                    output_tokens=tok_out,
                    total_tokens=tok_in + tok_out,
                    latency_ms=latency,
                    cost_usd=None,
                )

        choice  = data["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""

        # Reasoning-model fallback (GLM-4.7, GLM-5, DeepSeek-R1, o3-mini …)
        # These models put their answer in "reasoning" / "reasoning_content" and
        # leave "content" empty.  We surface the reasoning so the run is not lost.
        if not content.strip():
            reasoning = (
                message.get("reasoning")
                or message.get("reasoning_content")
                or ""
            )
            if reasoning:
                _log.warning(
                    "openrouter reasoning-only response  model=%s  "
                    "content=empty  reasoning_chars=%d  finish_reason=%s  "
                    "— using reasoning field as response content",
                    model, len(reasoning), choice.get("finish_reason", "?"),
                )
                content = f"[Reasoning]\n\n{reasoning}"

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
