"""Claude Code CLI adapter: wraps the `claude` CLI for development use.

Leverages Claude Code subscription billing for zero marginal cost during development.
Invokes `claude -p "<prompt>"` via subprocess.
"""

from __future__ import annotations
import asyncio
import subprocess
from spl.adapters.base import LLMAdapter, GenerationResult


class ClaudeCLIAdapter(LLMAdapter):
    """LLM adapter that wraps the Claude Code CLI.

    Usage:
        adapter = ClaudeCLIAdapter()
        result = await adapter.generate("What is 2+2?")

    This adapter is designed for development use, leveraging existing
    Claude Code subscription (flat billing = zero marginal cost per call).
    """

    def __init__(
        self,
        cli_path: str = "claude",
        timeout: int = 300,
        allowed_tools: list[str] | None = None,
    ):
        self.cli_path = cli_path
        self.timeout = timeout
        self.allowed_tools = allowed_tools or []

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate response by invoking claude CLI."""
        start = self._measure_time()

        # Build the full prompt with system message if provided
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"

        # Build CLI command
        cmd = [self.cli_path, "-p", full_prompt]
        if self.allowed_tools:
            cmd += ["--allowedTools", ",".join(self.allowed_tools)]

        # Run subprocess asynchronously
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude CLI not found at '{self.cli_path}'. "
                "Install Claude Code: https://docs.anthropic.com/en/docs/claude-code"
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Claude CLI timed out after {self.timeout}s")

        stderr_text = stderr.decode('utf-8', errors='replace').strip()

        if proc.returncode != 0:
            raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {stderr_text}")

        content = stdout.decode('utf-8', errors='replace').strip()
        latency = self._elapsed_ms(start)

        if not content:
            hint = f" stderr: {stderr_text[:300]}" if stderr_text else " (no stderr either)"
            raise RuntimeError(
                f"Claude CLI returned empty response (rc=0, latency={latency:.0f}ms).{hint}"
            )

        # Estimate tokens (Claude doesn't expose tokenizer publicly)
        input_tokens = len(full_prompt) // 4
        output_tokens = len(content) // 4

        return GenerationResult(
            content=content,
            model="claude-cli",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=0.0,  # Subscription billing
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Estimate tokens using character-based heuristic (~3.5 chars/token for Claude)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def list_models(self) -> list[str]:
        """Claude CLI uses whatever model is configured in the subscription."""
        return ["claude-cli"]
