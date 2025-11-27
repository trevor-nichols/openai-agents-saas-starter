"""Utilities for constructing prompt/runtime context objects."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.core.config import Settings, get_settings
from app.services.containers import ContainerService
from app.utils.tools.location import build_web_search_location


class InteractionContextBuilder:
    """Assemble the PromptRuntimeContext used by providers."""

    def __init__(
        self,
        *,
        container_service: ContainerService | None = None,
        settings_factory: Callable[[], Settings] = get_settings,
    ) -> None:
        self._container_service = container_service
        self._settings_factory = settings_factory

    async def build(
        self,
        *,
        actor,
        request: Any,
        conversation_id: str,
    ) -> PromptRuntimeContext:
        container_bindings = await self._resolve_container_bindings_for_tenant(
            tenant_id=actor.tenant_id
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
        )

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


__all__ = ["InteractionContextBuilder"]
