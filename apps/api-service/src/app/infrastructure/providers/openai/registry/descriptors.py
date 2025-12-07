"""Descriptor bookkeeping for OpenAI agents."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from agents import Agent

from app.agents._shared.specs import AgentSpec
from app.domain.ai import AgentDescriptor


class DescriptorStore:
    def __init__(self) -> None:
        self._descriptors: dict[str, AgentDescriptor] = {}

    def register(self, spec: AgentSpec, agent: Agent) -> AgentDescriptor:
        descriptor = AgentDescriptor(
            key=spec.key,
            display_name=spec.display_name,
            description=spec.description.strip(),
            model=str(agent.model),
            capabilities=spec.capabilities,
            last_seen_at=None,
            memory_strategy_defaults=spec.memory_strategy,
        )
        self._descriptors[spec.key] = descriptor
        return descriptor

    def get(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_key)

    def list(self) -> Sequence[AgentDescriptor]:
        return [self._descriptors[name] for name in sorted(self._descriptors.keys())]

    def mark_seen(self, agent_key: str, ts: datetime) -> None:
        descriptor = self._descriptors.get(agent_key)
        if descriptor:
            descriptor.last_seen_at = ts


__all__ = ["DescriptorStore"]
