"""Post-run finalization helpers for agent execution."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.services.agents.container_context import ContainerContextService
from app.services.agents.event_log import EventProjector
from app.services.agents.run_pipeline import (
    RunContext,
    project_compaction_events,
    project_new_session_items,
)
from app.services.agents.session_manager import SessionManager
from app.services.agents.usage import UsageService
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class RunFinalizer:
    """Finalize agent runs with persistence and telemetry updates."""

    def __init__(
        self,
        *,
        session_manager: SessionManager,
        usage_service: UsageService,
        container_context_service: ContainerContextService,
        event_projector: EventProjector,
        conversation_service: ConversationService,
    ) -> None:
        self._session_manager = session_manager
        self._usage_service = usage_service
        self._container_context_service = container_context_service
        self._event_projector = event_projector
        self._conversation_service = conversation_service

    async def finalize(
        self,
        *,
        ctx: RunContext,
        tenant_id: str,
        response_id: str | None,
        usage: Any,
    ) -> None:
        await self._sync_session_state(
            tenant_id=tenant_id,
            conversation_id=ctx.conversation_id,
            session_id=ctx.session_id,
            provider_name=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=tenant_id,
            conversation_id=ctx.conversation_id,
            response_id=response_id,
            usage=usage,
            agent_key=ctx.descriptor.key,
            provider_name=ctx.provider.name,
        )
        await self._append_container_context(
            ctx=ctx,
            tenant_id=tenant_id,
            response_id=response_id,
        )
        await project_compaction_events(
            event_projector=self._event_projector,
            compaction_events=ctx.compaction_events,
            conversation_id=ctx.conversation_id,
            tenant_id=tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=response_id,
        )
        await project_new_session_items(
            event_projector=self._event_projector,
            session_handle=ctx.session_handle,
            pre_items=ctx.pre_session_items,
            conversation_id=ctx.conversation_id,
            tenant_id=tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=response_id,
        )
        ctx.provider.mark_seen(ctx.descriptor.key, datetime.utcnow())

    async def _sync_session_state(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        session_id: str,
        provider_name: str | None,
        provider_conversation_id: str | None,
    ) -> None:
        await self._session_manager.sync_session_state(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            session_id=session_id,
            provider_name=provider_name,
            provider_conversation_id=provider_conversation_id,
        )

    async def _record_usage_metrics(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        response_id: str | None,
        usage: Any,
        agent_key: str | None,
        provider_name: str | None,
    ) -> None:
        await self._usage_service.record(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            response_id=response_id,
            usage=usage,
            agent_key=agent_key,
            provider=provider_name,
        )

    async def _append_container_context(
        self,
        *,
        ctx: RunContext,
        tenant_id: str,
        response_id: str | None,
    ) -> None:
        try:
            await self._container_context_service.append_run_events(
                conversation_service=self._conversation_service,
                conversation_id=ctx.conversation_id,
                tenant_id=tenant_id,
                agent_keys=[ctx.descriptor.key],
                runtime_ctx=ctx.runtime_ctx,
                response_id=response_id,
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "container_context.append_failed",
                extra={"tenant_id": tenant_id, "conversation_id": ctx.conversation_id},
                exc_info=exc,
            )
