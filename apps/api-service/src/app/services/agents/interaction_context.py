"""Utilities for constructing prompt/runtime context objects."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.registry_loader import load_agent_specs
from app.core.settings import Settings, get_settings
from app.services.agents.container_overrides import (
    ContainerOverrideError,
    ContainerOverrideResolver,
)
from app.services.agents.vector_store_overrides import (
    VectorStoreOverrideError,
    VectorStoreOverrideResolver,
)
from app.services.agents.vector_store_resolution import resolve_vector_store_ids_for_agent
from app.services.containers import ContainerService
from app.services.vector_stores.service import VectorStoreService
from app.utils.tools.location import build_web_search_location


class InteractionContextBuilder:
    """Assemble the PromptRuntimeContext used by providers."""

    def __init__(
        self,
        *,
        container_service: ContainerService | None = None,
        vector_store_service: VectorStoreService | None = None,
        settings_factory: Callable[[], Settings] = get_settings,
    ) -> None:
        self._container_service = container_service
        self._vector_store_service = vector_store_service
        self._settings_factory = settings_factory
        self._spec_index: dict[str, Any] | None = None
        self._container_override_resolver: ContainerOverrideResolver | None = None
        self._vector_store_override_resolver: VectorStoreOverrideResolver | None = None

    async def build(
        self,
        *,
        actor,
        request: Any,
        conversation_id: str,
        agent_keys: Iterable[str] | None = None,
    ) -> PromptRuntimeContext:
        container_bindings = await self._resolve_container_bindings_for_tenant(
            tenant_id=actor.tenant_id
        )
        container_overrides = await self._resolve_container_overrides(
            actor=actor,
            request=request,
            agent_keys=agent_keys,
        )
        file_search_keys = self._file_search_agent_keys(agent_keys)
        vector_store_overrides = await self._resolve_vector_store_overrides(
            actor=actor,
            request=request,
            agent_keys=file_search_keys,
        )
        file_search = (
            await self._resolve_file_search_for_agents(
                agent_keys=file_search_keys,
                actor=actor,
                request=request,
                overrides=vector_store_overrides,
            )
            if file_search_keys
            else None
        )
        return PromptRuntimeContext(
            actor=actor,
            conversation_id=conversation_id,
            request_message=request.message,
            settings=self._settings_factory(),
            user_location=build_web_search_location(
                request.location, share_location=request.share_location
            ),
            container_bindings=container_bindings,
            container_overrides=container_overrides,
            file_search=file_search,
            client_overrides=getattr(request, "context", None),
        )

    def _file_search_agent_keys(self, agent_keys: Iterable[str] | None) -> list[str]:
        """Return agent keys that may need file_search (requested + reachable delegates).

        We include the requested agents plus any agents reachable via agent_tool_keys or
        handoff_keys from those specs, so delegated agents also receive bindings.
        """

        if not agent_keys:
            return []

        specs = self._load_specs()
        queue = list(agent_keys)
        seen: set[str] = set()

        while queue:
            key = queue.pop(0)
            if key in seen:
                continue
            seen.add(key)
            spec = specs.get(key)
            if spec is None:
                continue
            # Agents as tools
            for dep in getattr(spec, "agent_tool_keys", ()) or ():
                if dep not in seen:
                    queue.append(dep)
            # Handoffs
            for dep in getattr(spec, "handoff_keys", ()) or ():
                if dep not in seen:
                    queue.append(dep)

        return list(seen)

    async def _resolve_container_bindings_for_tenant(
        self, *, tenant_id: str
    ) -> dict[str, str] | None:
        if not self._container_service:
            return None
        try:
            bindings = await self._container_service.list_agent_bindings(
                tenant_id=uuid.UUID(tenant_id)
            )
        except Exception:
            return None
        return bindings or None

    async def _resolve_container_overrides(
        self,
        *,
        actor,
        request: Any,
        agent_keys: Iterable[str] | None,
    ):
        overrides = getattr(request, "container_overrides", None)
        if not overrides or not isinstance(overrides, Mapping):
            return None
        if self._container_service is None:
            raise ContainerOverrideError("Container overrides require container service")
        if self._container_override_resolver is None:
            self._container_override_resolver = ContainerOverrideResolver(
                container_service=self._container_service
            )
        return await self._container_override_resolver.resolve(
            overrides=overrides,
            tenant_id=actor.tenant_id,
            allowed_agent_keys=agent_keys,
        )

    async def _resolve_vector_store_overrides(
        self,
        *,
        actor,
        request: Any,
        agent_keys: Iterable[str] | None,
    ) -> dict[str, list[str]] | None:
        overrides = getattr(request, "vector_store_overrides", None)
        if not overrides or not isinstance(overrides, Mapping):
            return None
        if self._vector_store_service is None:
            raise VectorStoreOverrideError("Vector store overrides require vector store service")
        if self._vector_store_override_resolver is None:
            self._vector_store_override_resolver = VectorStoreOverrideResolver(
                vector_store_service=self._vector_store_service,
                settings_factory=self._settings_factory,
                spec_index=self._spec_index,
            )
        return await self._vector_store_override_resolver.resolve(
            overrides=overrides,
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            allowed_agent_keys=agent_keys,
        )

    async def _resolve_file_search_for_agents(
        self,
        *,
        agent_keys: Iterable[str],
        actor,
        request: Any,
        overrides: Mapping[str, list[str]] | None = None,
    ) -> dict[str, Any] | None:
        """Resolve vector store bindings per agent for file_search."""

        svc = self._vector_store_service
        if svc is None:
            return None

        specs = self._load_specs()
        tenant_id = actor.tenant_id
        user_id = actor.user_id
        context_overrides = getattr(request, "context", None) or {}
        if isinstance(context_overrides, Mapping):
            context_overrides = dict(context_overrides)
        else:
            context_overrides = {}
        per_agent_overrides = overrides or {}
        result: dict[str, Any] = {}
        for key in agent_keys:
            spec = specs.get(key)
            if spec is None or "file_search" not in getattr(spec, "tool_keys", ()):
                continue
            override_ids = None
            if per_agent_overrides:
                override_ids = per_agent_overrides.get(key)
            if override_ids:
                vector_store_ids = list(override_ids)
            else:
                vector_store_ids = await self._resolve_vector_store_ids(
                    spec=spec,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    overrides=context_overrides,
                    vector_store_service=svc,
                )
            options = getattr(spec, "file_search_options", {}) or {}
            result[key] = {
                "vector_store_ids": vector_store_ids,
                "options": options,
            }
        return result or None

    def _load_specs(self) -> dict[str, Any]:
        if self._spec_index is None:
            self._spec_index = {spec.key: spec for spec in load_agent_specs()}
        return self._spec_index

    async def _resolve_vector_store_ids(
        self,
        *,
        spec,
        tenant_id: str,
        user_id: str | None,
        overrides: dict[str, Any],
        vector_store_service,
    ) -> list[str]:
        """Resolve the vector_store_ids for file_search following override > binding > default."""
        return await resolve_vector_store_ids_for_agent(
            spec=spec,
            tenant_id=tenant_id,
            user_id=user_id,
            overrides=overrides,
            vector_store_service=vector_store_service,
            settings_factory=self._settings_factory,
        )


__all__ = ["InteractionContextBuilder"]
