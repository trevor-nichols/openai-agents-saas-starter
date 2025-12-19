"""Agent-gated access checks for vector store uploads."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agents._shared.registry_loader import load_agent_specs
from app.core.settings import Settings, get_settings
from app.services.agents.vector_store_resolution import resolve_vector_store_ids_for_agent
from app.services.vector_stores.service import VectorStoreNotFoundError, VectorStoreService


class AgentVectorStoreAccessError(RuntimeError):
    """Raised when an agent is not authorized to use a vector store."""


class AgentVectorStoreAccessService:
    def __init__(
        self,
        *,
        vector_store_service: VectorStoreService,
        settings_factory: Callable[[], Settings] = get_settings,
    ) -> None:
        self._vector_store_service = vector_store_service
        self._settings_factory = settings_factory
        self._spec_index: dict[str, Any] | None = None

    async def assert_agent_can_attach(
        self,
        *,
        agent_key: str,
        tenant_id: str,
        user_id: str | None,
        vector_store_id: str,
    ) -> None:
        spec = self._load_specs().get(agent_key)
        if spec is None:
            raise AgentVectorStoreAccessError("Agent not found")
        if "file_search" not in getattr(spec, "tool_keys", ()):
            raise AgentVectorStoreAccessError("Agent does not support file_search")

        try:
            allowed = await resolve_vector_store_ids_for_agent(
                spec=spec,
                tenant_id=tenant_id,
                user_id=user_id,
                overrides=None,
                vector_store_service=self._vector_store_service,
                settings_factory=self._settings_factory,
            )
        except VectorStoreNotFoundError as exc:
            raise AgentVectorStoreAccessError(str(exc)) from exc

        store = await self._vector_store_service.get_store(
            vector_store_id=vector_store_id, tenant_id=tenant_id
        )
        openai_id = getattr(store, "openai_id", None)
        if not openai_id or str(openai_id) not in set(allowed):
            raise AgentVectorStoreAccessError("Vector store not allowed for this agent")

    def _load_specs(self) -> dict[str, Any]:
        if self._spec_index is None:
            self._spec_index = {spec.key: spec for spec in load_agent_specs()}
        return self._spec_index


__all__ = ["AgentVectorStoreAccessError", "AgentVectorStoreAccessService"]
