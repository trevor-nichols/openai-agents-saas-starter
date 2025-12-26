"""Per-agent vector store override resolution for file_search."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.agents._shared.registry_loader import load_agent_specs
from app.core.settings import Settings, get_settings
from app.services.agents.vector_store_resolution import resolve_vector_store_ids_for_agent
from app.services.vector_stores.service import VectorStoreService


class VectorStoreOverrideError(ValueError):
    """Raised when vector store overrides are invalid for the request."""


class VectorStoreOverrideResolver:
    def __init__(
        self,
        *,
        vector_store_service: VectorStoreService,
        settings_factory: Callable[[], Settings] | None = None,
        spec_index: Mapping[str, Any] | None = None,
    ) -> None:
        self._vector_store_service = vector_store_service
        self._settings_factory = settings_factory or get_settings
        self._spec_index: dict[str, Any] | None = dict(spec_index) if spec_index else None

    async def resolve(
        self,
        *,
        overrides: Mapping[str, Any] | None,
        tenant_id: str,
        user_id: str | None,
        allowed_agent_keys: Iterable[str] | None = None,
    ) -> dict[str, list[str]] | None:
        if not overrides:
            return None
        if not isinstance(overrides, Mapping):
            raise VectorStoreOverrideError("vector_store_overrides must be a mapping")

        allowed = set(allowed_agent_keys) if allowed_agent_keys is not None else None
        specs = self._load_specs()
        resolved: dict[str, list[str]] = {}

        for agent_key, override in overrides.items():
            if allowed is not None and agent_key not in allowed:
                raise VectorStoreOverrideError(
                    f"Agent '{agent_key}' is not part of this run"
                )
            spec = specs.get(agent_key)
            if spec is None:
                raise VectorStoreOverrideError(f"Agent '{agent_key}' not found")
            if "file_search" not in getattr(spec, "tool_keys", ()):
                raise VectorStoreOverrideError(
                    f"Agent '{agent_key}' does not support file_search"
                )

            payload = _coerce_override_payload(override)
            if not payload:
                raise VectorStoreOverrideError(
                    f"Agent '{agent_key}' override must include vector_store_id(s)"
                )
            if "vector_store_id" not in payload and "vector_store_ids" not in payload:
                raise VectorStoreOverrideError(
                    f"Agent '{agent_key}' override must include vector_store_id or vector_store_ids"
                )

            vector_store_ids = await resolve_vector_store_ids_for_agent(
                spec=spec,
                tenant_id=tenant_id,
                user_id=user_id,
                overrides=payload,
                vector_store_service=self._vector_store_service,
                settings_factory=self._settings_factory,
            )
            resolved[agent_key] = vector_store_ids

        return resolved or None

    def _load_specs(self) -> dict[str, Any]:
        if self._spec_index is None:
            self._spec_index = {spec.key: spec for spec in load_agent_specs()}
        return self._spec_index


def _coerce_override_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_payload"):
        payload = value.to_payload()
        if isinstance(payload, Mapping):
            return dict(payload)
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    return {}


__all__ = ["VectorStoreOverrideError", "VectorStoreOverrideResolver"]
