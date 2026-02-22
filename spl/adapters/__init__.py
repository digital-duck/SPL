"""LLM adapter registry and factory."""

from spl.adapters.base import LLMAdapter


_ADAPTER_REGISTRY: dict[str, type[LLMAdapter]] = {}


def register_adapter(name: str, adapter_cls: type[LLMAdapter]):
    """Register an LLM adapter by name."""
    _ADAPTER_REGISTRY[name] = adapter_cls


def get_adapter(name: str, **kwargs) -> LLMAdapter:
    """Get an LLM adapter instance by name."""
    if name not in _ADAPTER_REGISTRY:
        available = ", ".join(_ADAPTER_REGISTRY.keys())
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return _ADAPTER_REGISTRY[name](**kwargs)


def list_adapters() -> list[str]:
    """List registered adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def _register_builtin_adapters():
    from spl.adapters.claude_cli import ClaudeCLIAdapter
    from spl.adapters.openrouter import OpenRouterAdapter
    from spl.adapters.ollama import OllamaAdapter
    from spl.adapters.cloud_direct import CloudDirectAdapter
    register_adapter("claude_cli", ClaudeCLIAdapter)
    register_adapter("openrouter", OpenRouterAdapter)
    register_adapter("ollama", OllamaAdapter)
    register_adapter("cloud_direct", CloudDirectAdapter)


_register_builtin_adapters()
