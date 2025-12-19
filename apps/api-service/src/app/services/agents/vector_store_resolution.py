"""Shared helpers for resolving vector store bindings for agents."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.settings import Settings, get_settings
from app.services.vector_stores.service import VectorStoreNotFoundError


async def resolve_vector_store_ids_for_agent(
    *,
    spec,
    tenant_id: str,
    user_id: str | None,
    vector_store_service,
    settings_factory: Callable[[], Settings] = get_settings,
    overrides: dict[str, Any] | None = None,
) -> list[str]:
    """Resolve vector_store_ids for file_search: overrides -> binding -> spec -> tenant default."""

    overrides = overrides or {}

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

    try:
        binding = await vector_store_service.get_agent_binding(
            agent_key=spec.key,
            tenant_id=tenant_id,
        )
    except Exception:
        binding = None
    if binding is not None and getattr(binding, "openai_id", None):
        return [str(binding.openai_id)]

    binding_mode = getattr(spec, "vector_store_binding", "tenant_default")
    spec_ids = list(getattr(spec, "vector_store_ids", ()) or [])

    if binding_mode == "static":
        if not spec_ids:
            raise ValueError(
                "Agent "
                f"'{spec.key}' file_search requires vector_store_ids when binding='static'"
            )
        return spec_ids

    settings = settings_factory()
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


__all__ = ["resolve_vector_store_ids_for_agent"]
