"""Streaming agent chat orchestration."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Mapping
from typing import Any, cast

from agents import trace

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai.lifecycle import LifecycleEventBus
from app.domain.ai.models import AgentStreamEvent
from app.guardrails._shared.events import GuardrailEmissionToken, set_guardrail_emitters
from app.services.agents.asset_linker import AssetLinker
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import (
    ConversationActorContext,
    reset_current_actor,
    set_current_actor,
)
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.run_finalize import RunFinalizer
from app.services.agents.run_options import build_run_options
from app.services.agents.run_pipeline import (
    persist_assistant_message,
    prepare_run_context,
    record_user_message,
)
from app.services.agents.session_manager import SessionManager
from app.services.agents.streaming_pipeline import (
    AgentStreamProcessor,
    GuardrailStreamForwarder,
    build_guardrail_summary,
)
from app.services.agents.user_input import UserInputResolver
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ChatStreamOrchestrator:
    """Run a streaming agent interaction."""

    def __init__(
        self,
        *,
        provider_registry: AgentProviderRegistry,
        interaction_builder: InteractionContextBuilder,
        conversation_service: ConversationService,
        session_manager: SessionManager,
        attachment_service: AttachmentService,
        input_resolver: UserInputResolver,
        finalizer: RunFinalizer,
        asset_linker: AssetLinker,
    ) -> None:
        self._provider_registry = provider_registry
        self._interaction_builder = interaction_builder
        self._conversation_service = conversation_service
        self._session_manager = session_manager
        self._attachment_service = attachment_service
        self._input_resolver = input_resolver
        self._finalizer = finalizer
        self._asset_linker = asset_linker

    async def stream(
        self,
        request: AgentChatRequest,
        *,
        actor: ConversationActorContext,
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        lifecycle_bus = LifecycleEventBus()
        guardrail_events: list[Mapping[str, Any]] = []
        guardrail_token: GuardrailEmissionToken | None = None
        stream_handle = None

        async def _emit_compaction(event: AgentStreamEvent) -> None:
            await lifecycle_bus.emit(event)

        ctx = await prepare_run_context(
            actor=actor,
            request=request,
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            session_manager=self._session_manager,
            conversation_memory=await self._conversation_service.get_memory_config(
                request.conversation_id, tenant_id=actor.tenant_id
            )
            if request.conversation_id
            else None,
            compaction_emitter=_emit_compaction,
        )

        processor = AgentStreamProcessor(
            lifecycle_bus=lifecycle_bus,
            provider=ctx.provider,
            actor=actor,
            conversation_id=ctx.conversation_id,
            entrypoint_agent=ctx.descriptor.key,
            entrypoint_output_schema=ctx.descriptor.output_schema,
            attachment_service=self._attachment_service,
        )

        guardrail_forwarder = GuardrailStreamForwarder(
            lifecycle_bus=lifecycle_bus,
            conversation_id=ctx.conversation_id,
            default_agent=ctx.descriptor.key,
            get_current_agent=lambda: processor.outcome.current_agent or ctx.descriptor.key,
            get_last_response_id=lambda: processor.outcome.last_response_id,
            get_fallback_response_id=(
                lambda: getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None
            ),
        )
        guardrail_token = set_guardrail_emitters(
            emitter=guardrail_forwarder,
            collector=guardrail_events,
            context={
                "conversation_id": ctx.conversation_id,
                "agent": ctx.descriptor.key,
            },
        )

        agent_input, user_attachments = await self._input_resolver.resolve(
            request=request,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
        )
        _, user_message_id = await record_user_message(
            ctx=ctx,
            request=request,
            conversation_service=self._conversation_service,
            attachments=user_attachments,
        )
        if user_message_id is not None and user_attachments:
            await self._asset_linker.maybe_link_assets(
                tenant_id=actor.tenant_id,
                message_id=user_message_id,
                attachments=user_attachments,
            )

        token = set_current_actor(actor)
        try:
            logger.info(
                "agent.chat_stream.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": ctx.conversation_id,
                    "provider_conversation_id": ctx.provider_conversation_id,
                    "agent": ctx.descriptor.key,
                },
            )
            # When SDK sessions are in use, we rely on persisted session items for
            # continuation and disable provider-side conversation state to prevent
            # duplicate item ids being re-sent to the Responses API.
            runtime_conversation_id = None if ctx.session_handle is not None else (
                ctx.provider_conversation_id or ctx.conversation_id
            )
            run_options = build_run_options(request.run_options, hook_sink=lifecycle_bus)
            if (
                run_options is not None
                and ctx.session_handle is not None
                and run_options.previous_response_id
            ):
                logger.debug(
                    "agent.chat_stream.ignoring_previous_response_id_with_session",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": ctx.conversation_id,
                        "agent": ctx.descriptor.key,
                    },
                )
                run_options.previous_response_id = None

            with trace(workflow_name="Agent Chat Stream", group_id=ctx.conversation_id):
                stream_handle = ctx.provider.runtime.run_stream(
                    ctx.descriptor.key,
                    agent_input,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=run_options,
                )
                terminal_event: AgentStreamEvent | None = None
                async for event in processor.iter_events(stream_handle):
                    if event.is_terminal and event.kind != "error":
                        # Defer emitting the terminal event until after we persist the
                        # assistant message + sync session state. This keeps the public
                        # SSE `final` event aligned with durable storage and prevents
                        # client-side stream cancellation from skipping persistence.
                        terminal_event = event
                        break
                    yield event
        finally:
            reset_current_actor(token)
            if guardrail_token:
                guardrail_token.reset()

        if guardrail_events:
            summary_payload = build_guardrail_summary(guardrail_events)
            summary_event = AgentStreamEvent(
                kind="guardrail_result",
                conversation_id=ctx.conversation_id,
                agent=ctx.descriptor.key,
                guardrail_stage="summary",
                guardrail_name="Guardrail Summary",
                guardrail_key="guardrail_summary",
                guardrail_summary=True,
                payload=summary_payload,
            )
            if processor.outcome.current_output_schema is not None:
                summary_event.output_schema = processor.outcome.current_output_schema
            yield summary_event

        if terminal_event is not None and processor.pending_container_file_citations:
            container_attachments = await self._attachment_service.ingest_container_file_citations(
                processor.pending_container_file_citations,
                actor=actor,
                conversation_id=ctx.conversation_id,
                agent_key=ctx.descriptor.key,
                response_id=terminal_event.response_id
                or getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None,
            )
            if container_attachments:
                processor.outcome.attachments.extend(container_attachments)
                payloads = [
                    cast(Mapping[str, Any], self._attachment_service.to_attachment_payload(att))
                    for att in container_attachments
                ]
                if terminal_event.attachments is None:
                    terminal_event.attachments = payloads
                else:
                    terminal_event.attachments.extend(payloads)

        message_id = await persist_assistant_message(
            ctx=ctx,
            conversation_service=self._conversation_service,
            response_text=processor.outcome.complete_response,
            attachments=processor.outcome.attachments,
            active_agent=processor.outcome.current_agent or ctx.descriptor.key,
            handoff_count=processor.outcome.handoff_count or None,
        )
        await self._asset_linker.maybe_link_assets(
            tenant_id=actor.tenant_id,
            message_id=message_id,
            attachments=processor.outcome.attachments,
        )
        logger.info(
            "agent.chat_stream.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": ctx.conversation_id,
                "provider_conversation_id": ctx.provider_conversation_id,
                "agent": ctx.descriptor.key,
                "response_id": getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None,
            },
        )
        await self._finalizer.finalize(
            ctx=ctx,
            tenant_id=actor.tenant_id,
            response_id=getattr(stream_handle, "last_response_id", None)
            if stream_handle is not None
            else None,
            usage=getattr(stream_handle, "usage", None) if stream_handle is not None else None,
        )
        if terminal_event is not None:
            yield terminal_event


__all__ = ["ChatStreamOrchestrator"]
