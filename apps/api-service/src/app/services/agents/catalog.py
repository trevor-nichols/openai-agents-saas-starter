"""Agent catalog helpers kept separate from chat orchestration."""

from __future__ import annotations

import base64
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.api.v1.agents.schemas import AgentStatus, AgentSummary, AgentToolingFlags
from app.domain.ai import AgentDescriptor
from app.domain.ai.ports import AgentProvider
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.tooling import normalize_tool_overview, resolve_tooling_by_agent

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


@dataclass(slots=True)
class AgentCatalogPage:
    items: list[AgentSummary]
    next_cursor: str | None
    total: int


class AgentCatalogService:
    """Read-only catalog for available agents and tools."""

    def __init__(self, provider_registry: AgentProviderRegistry) -> None:
        self._providers = provider_registry

    def list_available_agents(self) -> list[AgentSummary]:
        """Return the first page of the catalog (default page size)."""

        return self.list_available_agents_page(
            limit=DEFAULT_PAGE_SIZE,
            cursor=None,
            search=None,
        ).items

    def list_available_agents_page(
        self, *, limit: int | None, cursor: str | None, search: str | None
    ) -> AgentCatalogPage:
        """
        Return a paginated slice of available agents.

        - limit: maximum number of items to return (None uses DEFAULT_PAGE_SIZE)
        - cursor: opaque position token from a previous response
        - search: optional case-insensitive match against name, display_name, description
        """
        provider = self._providers.get_default()
        descriptors = provider.list_agents()
        tooling_by_agent = self._resolve_tooling_by_agent(provider)
        filtered = self._apply_search(descriptors, search)
        ordered = self._sort_descriptors(filtered)

        page_size = self._normalize_limit(limit)
        start_index = self._resolve_start_index(ordered, cursor)
        end_index = start_index + page_size

        page_descriptors = ordered[start_index:end_index]
        next_cursor = (
            self._encode_cursor(page_descriptors[-1].key) if end_index < len(ordered) else None
        )

        return AgentCatalogPage(
            items=[
                self._to_summary(descriptor, tooling_by_agent.get(descriptor.key))
                for descriptor in page_descriptors
            ],
            next_cursor=next_cursor,
            total=len(ordered),
        )

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        provider = self._providers.get_default()
        descriptor = provider.get_agent(agent_name)
        if not descriptor:
            raise ValueError(f"Agent '{agent_name}' not found")
        tooling_by_agent = self._resolve_tooling_by_agent(provider)
        tooling = AgentToolingFlags.model_validate(tooling_by_agent.get(descriptor.key) or {})
        last_used = getattr(descriptor, "last_seen_at", None)
        if last_used:
            last_used = last_used.replace(microsecond=0).isoformat() + "Z"
        return AgentStatus(
            name=descriptor.key,
            status="active",
            output_schema=getattr(descriptor, "output_schema", None),
            last_used=last_used,
            total_conversations=0,
            tooling=tooling,
        )

    def get_tool_information(self) -> dict[str, Any]:
        provider = self._providers.get_default()
        return dict(provider.tool_overview())

    @staticmethod
    def _serialize_ts(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.replace(microsecond=0).isoformat() + "Z"

    def _to_summary(
        self, descriptor: AgentDescriptor, tooling: dict[str, bool] | None = None
    ) -> AgentSummary:
        return AgentSummary(
            name=descriptor.key,
            status=descriptor.status,
            description=descriptor.description,
            display_name=descriptor.display_name,
            model=descriptor.model,
            output_schema=getattr(descriptor, "output_schema", None),
            last_seen_at=self._serialize_ts(getattr(descriptor, "last_seen_at", None)),
            tooling=AgentToolingFlags.model_validate(tooling or {}),
        )

    @staticmethod
    def _sort_descriptors(
        descriptors: Iterable[AgentDescriptor],
    ) -> list[AgentDescriptor]:
        def _sort_key(desc: AgentDescriptor):
            label = (desc.display_name or desc.key or "").lower()
            return (label, desc.key)

        return sorted(descriptors, key=_sort_key)

    @staticmethod
    def _apply_search(
        descriptors: Iterable[AgentDescriptor],
        search: str | None,
    ) -> list[AgentDescriptor]:
        if not search:
            return list(descriptors)

        needle = search.lower()

        def _matches(desc: AgentDescriptor) -> bool:
            fields = [
                desc.display_name,
                desc.key,
                desc.description,
            ]
            return any(val and needle in val.lower() for val in fields)

        return [desc for desc in descriptors if _matches(desc)]

    @staticmethod
    def _normalize_limit(limit: int | None) -> int:
        if limit is None:
            return DEFAULT_PAGE_SIZE
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return min(limit, MAX_PAGE_SIZE)

    def _resolve_start_index(
        self,
        descriptors: list[AgentDescriptor],
        cursor: str | None,
    ) -> int:
        if cursor is None:
            return 0
        target = self._decode_cursor(cursor)
        for idx, descriptor in enumerate(descriptors):
            if descriptor.key == target:
                return idx + 1
        raise ValueError("Invalid pagination cursor")

    @staticmethod
    def _encode_cursor(agent_key: str) -> str:
        payload = {"agent": agent_key}
        raw = json.dumps(payload).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    @staticmethod
    def _decode_cursor(cursor: str) -> str:
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
            agent = data.get("agent")
            if not isinstance(agent, str) or not agent:
                raise ValueError("Invalid pagination cursor")
            return agent
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid pagination cursor") from exc

    @staticmethod
    def _resolve_tooling_by_agent(provider: AgentProvider) -> dict[str, dict[str, bool]]:
        overview = provider.tool_overview()
        per_agent = normalize_tool_overview(overview)
        return resolve_tooling_by_agent(per_agent)


__all__ = ["AgentCatalogService", "AgentCatalogPage"]
