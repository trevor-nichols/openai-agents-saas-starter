"""Non-streaming agent chat orchestration."""

from __future__ import annotations

import logging
from typing import Any

from agents import trace

from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, MessageAttachment
from app.domain.ai.models import AgentStreamEvent
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
from app.services.agents.user_input import UserInputResolver
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ChatRunOrchestrator:
    """Run a single non-streaming agent interaction."""

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

    async def run(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
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
                "agent.chat.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": ctx.conversation_id,
                    "provider_conversation_id": ctx.provider_conversation_id,
                    "agent": ctx.descriptor.key,
                },
            )
            # For non-stream runs we keep a stable, local conversation id for trace
            # grouping. Continuation is driven by the persisted SDK session items.
            runtime_conversation_id = ctx.conversation_id
            run_options = build_run_options(request.run_options)
            if (
                run_options is not None
                and ctx.session_handle is not None
                and run_options.previous_response_id
            ):
                logger.debug(
                    "agent.chat.ignoring_previous_response_id_with_session",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": ctx.conversation_id,
                        "agent": ctx.descriptor.key,
                    },
                )
                run_options.previous_response_id = None
            with trace(workflow_name="Agent Chat", group_id=ctx.conversation_id):
                result = await ctx.provider.runtime.run(
                    ctx.descriptor.key,
                    agent_input,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=run_options,
                )
        finally:
            reset_current_actor(token)

        response_text = result.response_text or str(result.final_output)
        image_attachments = await self._attachment_service.ingest_image_outputs(
            result.tool_outputs,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
            response_id=result.response_id,
        )
        container_attachments = await self._attachment_service.ingest_container_file_citations(
            result.tool_outputs,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
            response_id=result.response_id,
        )
        attachments = [*image_attachments, *container_attachments]
        message_id = await persist_assistant_message(
            ctx=ctx,
            conversation_service=self._conversation_service,
            response_text=response_text,
            attachments=attachments,
            active_agent=result.final_agent,
            handoff_count=result.handoff_count,
        )
        await self._asset_linker.maybe_link_assets(
            tenant_id=actor.tenant_id,
            message_id=message_id,
            attachments=attachments,
        )
        logger.info(
            "agent.chat.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": ctx.conversation_id,
                "provider_conversation_id": ctx.provider_conversation_id,
                "agent": ctx.descriptor.key,
                "response_id": result.response_id,
            },
        )
        await self._finalizer.finalize(
            ctx=ctx,
            tenant_id=actor.tenant_id,
            response_id=result.response_id,
            usage=result.usage,
        )

        def _resolve_output_schema(agent_key: str | None) -> Any:
            if not agent_key:
                return ctx.descriptor.output_schema
            descriptor = ctx.provider.get_agent(agent_key)
            if descriptor:
                return descriptor.output_schema
            return ctx.descriptor.output_schema

        effective_schema = _resolve_output_schema(result.final_agent or ctx.descriptor.key)
        return AgentChatResponse(
            response=response_text,
            structured_output=AgentStreamEvent._strip_unserializable(result.structured_output),
            output_schema=effective_schema,
            conversation_id=ctx.conversation_id,
            agent_used=result.final_agent or ctx.descriptor.key,
            handoff_occurred=bool(result.handoff_count),
            attachments=[
                MessageAttachment(**self._attachment_service.to_attachment_schema(att))
                for att in attachments
            ],
            metadata={
                "model_used": ctx.descriptor.model,
                **self._attachment_service.attachment_metadata_note(attachments),
            },
        )


__all__ = ["ChatRunOrchestrator"]
