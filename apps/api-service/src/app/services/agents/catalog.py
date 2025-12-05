"""Agent catalog helpers kept separate from chat orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.services.agents.provider_registry import AgentProviderRegistry


class AgentCatalogService:
    """Read-only catalog for available agents and tools."""

    def __init__(self, provider_registry: AgentProviderRegistry) -> None:
        self._providers = provider_registry

    def list_available_agents(self) -> list[AgentSummary]:
        provider = self._providers.get_default()

        def _serialize_ts(dt: datetime | None) -> str | None:
            if dt is None:
                return None
            return dt.replace(microsecond=0).isoformat() + "Z"

        return [
            AgentSummary(
                name=descriptor.key,
                status=descriptor.status,
                description=descriptor.description,
                display_name=descriptor.display_name,
                model=descriptor.model,
                last_seen_at=_serialize_ts(getattr(descriptor, "last_seen_at", None)),
            )
            for descriptor in provider.list_agents()
        ]

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        provider = self._providers.get_default()
        descriptor = provider.get_agent(agent_name)
        if not descriptor:
            raise ValueError(f"Agent '{agent_name}' not found")
        last_used = getattr(descriptor, "last_seen_at", None)
        if last_used:
            last_used = last_used.replace(microsecond=0).isoformat() + "Z"
        return AgentStatus(
            name=descriptor.key,
            status="active",
            last_used=last_used,
            total_conversations=0,
        )

    def get_tool_information(self) -> dict[str, Any]:
        provider = self._providers.get_default()
        return dict(provider.tool_overview())


__all__ = ["AgentCatalogService"]
