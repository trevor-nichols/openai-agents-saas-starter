"""Shared orchestration helpers for agent runs.

These utilities keep AgentService lean by centralizing the pre/post run
work (session prep, message persistence, telemetry projection). They are
intentionally side-effect free beyond the collaborators passed in, so they
stay easy to unit test.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.infrastructure.providers.openai.memory import MemoryStrategy
from app.observability.metrics import MEMORY_COMPACTION_ITEMS_TOTAL
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.memory_strategy import (
    DEFAULT_SUMMARY_MAX_AGE_SECONDS,
    build_memory_strategy_config,
    load_cross_session_summary,
    memory_cfg_to_mapping,
    resolve_memory_injection,
)
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.session_items import compute_session_delta, get_session_items
from app.services.agents.session_manager import SessionManager
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RunContext:
    actor: ConversationActorContext
    provider: Any
    descriptor: Any
    conversation_id: str
    session_id: str
    session_handle: Any
    provider_conversation_id: str | None
    runtime_ctx: Any
    pre_session_items: list[dict[str, Any]]
    existing_state: Any
    compaction_events: list[AgentStreamEvent] = field(default_factory=list)


async def prepare_run_context(
    *,
    actor: ConversationActorContext,
    request: AgentChatRequest,
    provider_registry: AgentProviderRegistry,
    interaction_builder: InteractionContextBuilder,
    conversation_service: ConversationService,
    session_manager: SessionManager,
    provider_conversation_id: str | None = None,
    conversation_memory: Any | None = None,
    compaction_emitter: Callable[[AgentStreamEvent], Awaitable[None]] | None = None,
) -> RunContext:
    """Resolve provider + session state used by both sync and streaming flows."""

    provider = provider_registry.get_default()
    descriptor = provider.resolve_agent(request.agent_type)
    conversation_id = request.conversation_id or str(uuid.uuid4())

    runtime_ctx = await interaction_builder.build(
        actor=actor,
        request=request,
        conversation_id=conversation_id,
        agent_keys=[descriptor.key],
    )
    compaction_events: list[AgentStreamEvent] = []
    conversation_defaults = memory_cfg_to_mapping(conversation_memory)
    memory_cfg = build_memory_strategy_config(
        request,
        conversation_defaults=conversation_defaults,
        agent_defaults=getattr(descriptor, "memory_strategy_defaults", None),
    )
    # Cross-session memory injection (prompt-level)
    inject_memory = resolve_memory_injection(
        request,
        conversation_defaults=conversation_defaults,
        agent_defaults=getattr(descriptor, "memory_strategy_defaults", None),
    )
    if inject_memory and request.conversation_id:
        summary_text = await load_cross_session_summary(
            conversation_id=request.conversation_id,
            tenant_id=actor.tenant_id,
            agent_key=descriptor.key,
            conversation_service=conversation_service,
            max_age_seconds=DEFAULT_SUMMARY_MAX_AGE_SECONDS,
            max_chars=(memory_cfg.summary_max_chars if memory_cfg else 4000),
        )
        if summary_text:
            runtime_ctx.memory_summary = summary_text
    existing_state = await conversation_service.get_session_state(
        conversation_id, tenant_id=actor.tenant_id
    )

    async def _on_compaction(payload: Mapping[str, Any]) -> None:
        event = AgentStreamEvent(
            kind="lifecycle",
            event="memory_compaction",
            run_item_type="memory_compaction",
            agent=descriptor.key,
            conversation_id=conversation_id,
            payload=dict(payload),
        )
        if compaction_emitter:
            await compaction_emitter(event)
        compaction_events.append(event)
        try:
            inputs = int(payload.get("compacted_inputs", 0))
            outputs = int(payload.get("compacted_outputs", 0))
            if inputs:
                MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="input").inc(inputs)
            if outputs:
                MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="output").inc(outputs)
        except Exception:
            pass

    session_id, session_handle = await session_manager.acquire_session(
        provider,
        actor.tenant_id,
        conversation_id,
        provider_conversation_id,
        memory_strategy=memory_cfg,
        agent_key=descriptor.key,
        on_compaction=(
            _on_compaction if memory_cfg and memory_cfg.mode == MemoryStrategy.COMPACT else None
        ),
    )

    pre_session_items = await get_session_items(session_handle)

    return RunContext(
        actor=actor,
        provider=provider,
        descriptor=descriptor,
        conversation_id=conversation_id,
        session_id=session_id,
        session_handle=session_handle,
        provider_conversation_id=provider_conversation_id,
        runtime_ctx=runtime_ctx,
        pre_session_items=pre_session_items,
        existing_state=existing_state,
        compaction_events=compaction_events,
    )


async def record_user_message(
    *,
    ctx: RunContext,
    request: AgentChatRequest,
    conversation_service: ConversationService,
) -> ConversationMetadata:
    """Persist the inbound user message with consistent metadata."""

    metadata = build_metadata(
        tenant_id=ctx.actor.tenant_id,
        provider=ctx.provider.name,
        provider_conversation_id=ctx.provider_conversation_id,
        agent_entrypoint=request.agent_type or ctx.descriptor.key,
        active_agent=ctx.descriptor.key,
        session_id=ctx.session_id,
        user_id=ctx.actor.user_id,
    )
    user_message = ConversationMessage(role="user", content=request.message)
    await conversation_service.append_message(
        ctx.conversation_id,
        user_message,
        tenant_id=ctx.actor.tenant_id,
        metadata=metadata,
    )

    if hasattr(conversation_service, "record_conversation_created"):
        await conversation_service.record_conversation_created(
            ctx.conversation_id,
            tenant_id=ctx.actor.tenant_id,
            agent_entrypoint=request.agent_type or ctx.descriptor.key,
            existed=ctx.existing_state is not None,
        )

    return metadata


async def persist_assistant_message(
    *,
    ctx: RunContext,
    conversation_service: ConversationService,
    response_text: str,
    attachments,
    active_agent: str | None = None,
    handoff_count: int | None = None,
) -> int | None:
    """Store assistant response with aligned metadata."""

    agent_name = active_agent or ctx.descriptor.key
    assistant_message = ConversationMessage(
        role="assistant",
        content=response_text,
        attachments=attachments,
    )
    return await conversation_service.append_message(
        ctx.conversation_id,
        assistant_message,
        tenant_id=ctx.actor.tenant_id,
        metadata=build_metadata(
            tenant_id=ctx.actor.tenant_id,
            provider=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
            agent_entrypoint=ctx.descriptor.key,
            active_agent=agent_name,
            session_id=ctx.session_id,
            user_id=ctx.actor.user_id,
            handoff_count=handoff_count,
        ),
    )


async def project_new_session_items(
    *,
    event_projector: EventProjector,
    session_handle: Any,
    pre_items: list[dict[str, Any]],
    conversation_id: str,
    tenant_id: str,
    agent: str | None,
    model: str | None,
    response_id: str | None,
    workflow_run_id: str | None = None,
) -> None:
    """Ingest newly created session items into the event log (best-effort)."""

    post_items = await get_session_items(session_handle)
    if not post_items:
        return

    delta = compute_session_delta(pre_items, post_items)
    if not delta:
        if len(post_items) != len(pre_items):
            logging.getLogger(__name__).debug(
                "session_delta_empty_after_rewrite",
                extra={
                    "pre_len": len(pre_items),
                    "post_len": len(post_items),
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
        return
    try:
        await event_projector.ingest_session_items(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            session_items=delta,
            agent=agent,
            model=model,
            response_id=response_id,
            workflow_run_id=workflow_run_id,
        )
    except Exception:  # pragma: no cover - defensive, best-effort
        logging.getLogger(__name__).exception(
            "event_projection_failed",
            extra={
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "agent": agent,
            },
        )


async def project_compaction_events(
    *,
    event_projector: EventProjector,
    compaction_events: list[AgentStreamEvent],
    conversation_id: str,
    tenant_id: str,
    agent: str | None,
    model: str | None,
    response_id: str | None,
    workflow_run_id: str | None = None,
) -> None:
    """Persist compaction lifecycle events into the event log (best-effort)."""

    if not compaction_events:
        return
    try:
        await event_projector.ingest_session_items(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            session_items=[AgentStreamEvent._to_mapping(ev) or {} for ev in compaction_events],
            agent=agent,
            model=model,
            response_id=response_id,
            workflow_run_id=workflow_run_id,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "compaction_event_projection_failed",
            extra={
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
            },
        )


def build_metadata(
    *,
    tenant_id: str,
    provider: str | None,
    provider_conversation_id: str | None,
    agent_entrypoint: str,
    active_agent: str,
    session_id: str,
    user_id: str,
    handoff_count: int | None = None,
) -> ConversationMetadata:
    return ConversationMetadata(
        tenant_id=tenant_id,
        provider=provider,
        provider_conversation_id=provider_conversation_id,
        agent_entrypoint=agent_entrypoint,
        active_agent=active_agent,
        handoff_count=handoff_count,
        sdk_session_id=session_id,
        user_id=user_id,
    )


__all__ = [
    "RunContext",
    "prepare_run_context",
    "record_user_message",
    "persist_assistant_message",
    "project_new_session_items",
    "project_compaction_events",
    "build_metadata",
]
