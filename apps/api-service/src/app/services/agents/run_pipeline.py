"""Shared orchestration helpers for agent runs.

These utilities keep AgentService lean by centralizing the pre/post run
work (session prep, message persistence, telemetry projection). They are
intentionally side-effect free beyond the collaborators passed in, so they
stay easy to unit test.
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.session_manager import SessionManager
from app.services.conversation_service import ConversationService


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


async def prepare_run_context(
    *,
    actor: ConversationActorContext,
    request: AgentChatRequest,
    provider_registry: AgentProviderRegistry,
    interaction_builder: InteractionContextBuilder,
    conversation_service: ConversationService,
    session_manager: SessionManager,
    provider_conversation_id: str | None = None,
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
    existing_state = await conversation_service.get_session_state(
        conversation_id, tenant_id=actor.tenant_id
    )

    session_id, session_handle = await session_manager.acquire_session(
        provider,
        actor.tenant_id,
        conversation_id,
        provider_conversation_id,
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
) -> None:
    """Store assistant response with aligned metadata."""

    assistant_message = ConversationMessage(
        role="assistant",
        content=response_text,
        attachments=attachments,
    )
    await conversation_service.append_message(
        ctx.conversation_id,
        assistant_message,
        tenant_id=ctx.actor.tenant_id,
        metadata=build_metadata(
            tenant_id=ctx.actor.tenant_id,
            provider=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
            agent_entrypoint=ctx.descriptor.key,
            active_agent=ctx.descriptor.key,
            session_id=ctx.session_id,
            user_id=ctx.actor.user_id,
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
    delta = post_items[len(pre_items) :]
    if not delta:
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
        import logging

        logging.getLogger(__name__).exception(
            "event_projection_failed",
            extra={
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "agent": agent,
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
) -> ConversationMetadata:
    return ConversationMetadata(
        tenant_id=tenant_id,
        provider=provider,
        provider_conversation_id=provider_conversation_id,
        agent_entrypoint=agent_entrypoint,
        active_agent=active_agent,
        sdk_session_id=session_id,
        user_id=user_id,
    )


async def get_session_items(session_handle: Any) -> list[dict[str, Any]]:
    """Safely read items from a provider session handle."""

    getter = getattr(session_handle, "get_items", None)
    if getter is None or not callable(getter):
        return []
    try:
        result = getter()
        items = await result if inspect.isawaitable(result) else result
        if items is None or not isinstance(items, Iterable):
            return []
        return list(items)
    except Exception:  # pragma: no cover - defensive
        import logging

        logging.getLogger(__name__).exception(
            "session_items_fetch_failed",
        )
        return []


__all__ = [
    "RunContext",
    "prepare_run_context",
    "record_user_message",
    "persist_assistant_message",
    "project_new_session_items",
    "build_metadata",
    "get_session_items",
]
