"""Container override resolution for agent runs."""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from typing import Any

from app.agents._shared.prompt_context import ContainerOverrideContext
from app.agents._shared.registry_loader import load_agent_specs
from app.services.containers import ContainerNotFoundError, ContainerService


class ContainerOverrideError(ValueError):
    """Raised when container overrides are invalid for the request."""


class ContainerOverrideResolver:
    def __init__(self, *, container_service: ContainerService) -> None:
        self._container_service = container_service
        self._spec_index: dict[str, Any] | None = None

    async def resolve(
        self,
        *,
        overrides: Mapping[str, str] | None,
        tenant_id: str,
        allowed_agent_keys: Iterable[str] | None = None,
    ) -> dict[str, ContainerOverrideContext] | None:
        if not overrides:
            return None

        allowed = set(allowed_agent_keys) if allowed_agent_keys is not None else None
        specs = self._load_specs()
        tenant_uuid = _coerce_uuid(tenant_id, "tenant_id")
        resolved: dict[str, ContainerOverrideContext] = {}

        for agent_key, container_id in overrides.items():
            if allowed is not None and agent_key not in allowed:
                raise ContainerOverrideError(
                    f"Agent '{agent_key}' is not part of this run"
                )

            spec = specs.get(agent_key)
            if spec is None:
                raise ContainerOverrideError(f"Agent '{agent_key}' not found")
            if "code_interpreter" not in getattr(spec, "tool_keys", ()):
                raise ContainerOverrideError(
                    f"Agent '{agent_key}' does not support code_interpreter"
                )

            container_uuid = _coerce_uuid(container_id, "container_id")
            try:
                container = await self._container_service.get_container(
                    container_id=container_uuid, tenant_id=tenant_uuid
                )
            except ContainerNotFoundError as exc:
                raise ContainerOverrideError(
                    f"Container '{container_id}' not found"
                ) from exc

            openai_id = getattr(container, "openai_id", None)
            if not openai_id:
                raise ContainerOverrideError(
                    f"Container '{container_id}' is missing an OpenAI id"
                )

            resolved[agent_key] = ContainerOverrideContext(
                container_id=str(container.id),
                openai_container_id=str(openai_id),
            )

        return resolved or None

    def _load_specs(self) -> dict[str, Any]:
        if self._spec_index is None:
            self._spec_index = {spec.key: spec for spec in load_agent_specs()}
        return self._spec_index


def _coerce_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except Exception as exc:
        raise ContainerOverrideError(f"Invalid {field_name}") from exc


__all__ = ["ContainerOverrideError", "ContainerOverrideResolver"]
