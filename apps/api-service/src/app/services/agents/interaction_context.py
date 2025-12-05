"""Utilities for constructing prompt/runtime context objects."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from typing import Any

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.registry_loader import load_agent_specs
from app.core.settings import Settings, get_settings
from app.services.containers import ContainerService
from app.services.vector_stores.service import VectorStoreNotFoundError, VectorStoreService
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
        file_search_keys = self._file_search_agent_keys(agent_keys)
        file_search = (
            await self._resolve_file_search_for_agents(
                agent_keys=file_search_keys,
                actor=actor,
                request=request,
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

    async def _resolve_file_search_for_agents(
        self,
        *,
        agent_keys: Iterable[str],
        actor,
        request: Any,
    ) -> dict[str, Any] | None:
        """Resolve vector store bindings per agent for file_search."""

        svc = self._vector_store_service
        if svc is None:
            return None

        specs = self._load_specs()
        tenant_id = actor.tenant_id
        user_id = actor.user_id
        overrides = getattr(request, "context", None) or {}
        result: dict[str, Any] = {}
        for key in agent_keys:
            spec = specs.get(key)
            if spec is None or "file_search" not in getattr(spec, "tool_keys", ()):
                continue
            vector_store_ids = await self._resolve_vector_store_ids(
                spec=spec,
                tenant_id=tenant_id,
                user_id=user_id,
                overrides=overrides,
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
        user_id: str,
        overrides: dict[str, Any],
        vector_store_service,
    ) -> list[str]:
        """Resolve the vector_store_ids for file_search following override > binding > default."""

        # Request override (client-provided)
        override_ids = overrides.get("vector_store_ids") or overrides.get("vector_store_id")
        if override_ids:
            if isinstance(override_ids, str):
                override_ids = [override_ids]
            resolved: list[str] = []
            for candidate in override_ids:
                store = None
                try:
                    store = await vector_store_service.get_store(
                        vector_store_id=candidate, tenant_id=tenant_id
                    )
                except Exception:
                    store = await vector_store_service.get_store_by_openai_id(
                        tenant_id=tenant_id, openai_id=str(candidate)
                    )
                if store is None:
                    raise VectorStoreNotFoundError("Vector store override not found")
                resolved.append(str(store.openai_id))
            return resolved

        # Agent-level binding stored in DB
        try:
            binding = await vector_store_service.get_agent_binding(
                agent_key=spec.key,
                tenant_id=tenant_id,
            )
        except Exception:
            binding = None
        if binding is not None and getattr(binding, "openai_id", None):
            return [str(binding.openai_id)]

        # Spec-configured bindings
        binding_mode = getattr(spec, "vector_store_binding", "tenant_default")
        spec_ids = list(getattr(spec, "vector_store_ids", ()) or [])

        if binding_mode == "static":
            if not spec_ids:
                raise ValueError(
                    "Agent "
                    f"'{spec.key}' file_search requires vector_store_ids when binding='static'"
                )
            return spec_ids

        settings = self._settings_factory()
        auto_create = getattr(settings, "auto_create_vector_store_for_file_search", True)

        if binding_mode == "required":
            store = await vector_store_service.get_store_by_name(
                tenant_id=tenant_id,
                name="primary",
            )
            if store is None or not store.openai_id:
                raise VectorStoreNotFoundError("Primary vector store is required but not found")
            return [str(store.openai_id)]

        if auto_create:
            store = await vector_store_service.ensure_primary_store(
                tenant_id=tenant_id,
                owner_user_id=user_id,
            )
        else:
            store = await vector_store_service.get_store_by_name(
                tenant_id=tenant_id,
                name="primary",
            )

        if store is None or not getattr(store, "openai_id", None):
            raise VectorStoreNotFoundError("Failed to resolve vector store for file_search")
        return [str(store.openai_id)]


__all__ = ["InteractionContextBuilder"]
