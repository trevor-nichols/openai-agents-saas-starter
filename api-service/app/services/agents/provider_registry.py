"""In-memory registry for agent providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from app.domain.ai import AgentProvider


@dataclass(slots=True)
class AgentProviderRegistry:
    """Keeps track of configured providers and the default selection."""

    _providers: Dict[str, AgentProvider] = field(default_factory=dict)
    _default_key: str | None = None

    def register(self, provider: AgentProvider, *, set_default: bool = False) -> None:
        key = provider.name
        self._providers[key] = provider
        if set_default or self._default_key is None:
            self._default_key = key

    def get(self, name: str) -> AgentProvider:
        try:
            return self._providers[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Agent provider '{name}' is not registered") from exc

    def get_default(self) -> AgentProvider:
        if not self._default_key:
            raise RuntimeError("No agent providers registered; call register() during bootstrap.")
        return self._providers[self._default_key]

    def clear(self) -> None:
        self._providers.clear()
        self._default_key = None


_REGISTRY: AgentProviderRegistry | None = None


def get_provider_registry() -> AgentProviderRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AgentProviderRegistry()
    return _REGISTRY


def reset_provider_registry() -> AgentProviderRegistry:
    global _REGISTRY
    _REGISTRY = AgentProviderRegistry()
    return _REGISTRY


__all__ = [
    "AgentProviderRegistry",
    "get_provider_registry",
    "reset_provider_registry",
]
