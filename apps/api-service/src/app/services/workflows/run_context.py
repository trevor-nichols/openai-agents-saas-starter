"""Build workflow execution context and bootstrap run state."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from app.api.v1.shared.attachments import InputAttachment
from app.domain.conversations import (
    ConversationAttachment,
    ConversationMessage,
    ConversationMetadata,
)
from app.domain.input_attachments import InputAttachmentRef
from app.services.agents.container_context import ContainerContextService
from app.services.agents.context import ConversationActorContext
from app.services.agents.input_attachments import InputAttachmentService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.assets.service import AssetService
from app.services.conversation_service import ConversationService
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.utils import first_agent_key, workflow_agent_keys
from app.workflows._shared.specs import WorkflowSpec

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkflowRunContext:
    run_id: str
    workflow: WorkflowSpec
    provider: Any
    session_handle: Any
    entry_agent: str
    agent_input: Any
    runtime_ctx: Any
    conversation_id: str
    actor: ConversationActorContext


class WorkflowRunBootstrapper:
    def __init__(
        self,
        *,
        provider_registry: AgentProviderRegistry,
        interaction_builder: InteractionContextBuilder,
        conversation_service: ConversationService,
        recorder: WorkflowRunRecorder,
        container_context_service: ContainerContextService,
        input_attachment_service: InputAttachmentService | None = None,
        asset_service: AssetService | None = None,
    ) -> None:
        self._provider_registry = provider_registry
        self._interaction_builder = interaction_builder
        self._conversation_service = conversation_service
        self._input_attachment_service = input_attachment_service
        self._asset_service = asset_service
        self._recorder = recorder
        self._container_context_service = container_context_service

    async def prepare(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        attachments: list[InputAttachment] | None,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
        container_overrides: dict[str, str] | None = None,
        vector_store_overrides: Mapping[str, Any] | None = None,
    ) -> WorkflowRunContext:
        provider = self._provider_registry.get_default()
        run_id = str(uuid.uuid4())
        entry_agent = first_agent_key(workflow) or workflow.key
        session_handle = provider.session_store.build(conversation_id)
        conversation_exists = await self._conversation_service.conversation_exists(
            conversation_id, tenant_id=actor.tenant_id
        )

        agent_input, user_attachments = await self._resolve_user_input(
            attachments=attachments,
            actor=actor,
            conversation_id=conversation_id,
            agent_key=entry_agent,
            message=message,
        )
        message_id = await self._conversation_service.append_message(
            conversation_id,
            ConversationMessage(role="user", content=message, attachments=user_attachments),
            tenant_id=actor.tenant_id,
            metadata=ConversationMetadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=workflow.key,
                active_agent=entry_agent,
                provider=provider.name,
                user_id=actor.user_id,
            ),
        )
        if self._asset_service and message_id is not None and user_attachments:
            try:
                storage_ids = [uuid.UUID(att.object_id) for att in user_attachments]
                await self._asset_service.link_assets_to_message(
                    tenant_id=uuid.UUID(actor.tenant_id),
                    message_id=message_id,
                    storage_object_ids=storage_ids,
                )
            except Exception as exc:
                logger.warning(
                    "workflow.user_attachment.link_failed",
                    extra={"tenant_id": actor.tenant_id, "conversation_id": conversation_id},
                    exc_info=exc,
                )

        await self._conversation_service.record_conversation_created(
            conversation_id,
            tenant_id=actor.tenant_id,
            agent_entrypoint=workflow.key,
            existed=conversation_exists,
        )

        runtime_ctx = await self._interaction_builder.build(
            actor=actor,
            request=_WorkflowRequestProxy(
                message=message,
                location=location,
                share_location=share_location,
                container_overrides=container_overrides,
                vector_store_overrides=vector_store_overrides,
            ),
            conversation_id=conversation_id,
            agent_keys=workflow_agent_keys(workflow),
        )
        await self._bootstrap_run_record(
            run_id=run_id,
            workflow=workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
            runtime_ctx=runtime_ctx,
        )

        return WorkflowRunContext(
            run_id=run_id,
            workflow=workflow,
            provider=provider,
            session_handle=session_handle,
            entry_agent=entry_agent,
            agent_input=agent_input,
            runtime_ctx=runtime_ctx,
            conversation_id=conversation_id,
            actor=actor,
        )

    async def _resolve_user_input(
        self,
        *,
        attachments: list[InputAttachment] | None,
        actor: ConversationActorContext,
        conversation_id: str,
        agent_key: str,
        message: str,
    ) -> tuple[Any, list[ConversationAttachment]]:
        if not attachments:
            return message, []
        if self._input_attachment_service is None:
            raise RuntimeError("InputAttachmentService is not configured")
        attachment_refs = [
            InputAttachmentRef(object_id=att.object_id, kind=getattr(att, "kind", None))
            for att in attachments
        ]
        resolution = await self._input_attachment_service.resolve(
            attachment_refs,
            actor=actor,
            conversation_id=conversation_id,
            agent_key=agent_key,
        )
        if not resolution.input_items:
            return message, resolution.attachments
        content: list[dict[str, Any]] = [
            {"type": "input_text", "text": message},
            *resolution.input_items,
        ]
        return [{"role": "user", "content": content}], resolution.attachments

    async def _bootstrap_run_record(
        self,
        *,
        run_id: str,
        workflow: WorkflowSpec,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
        runtime_ctx,
    ) -> None:
        agent_keys = workflow_agent_keys(workflow)
        contexts: dict[str, dict[str, str | None]] = {}
        metadata: dict[str, Any] | None = None
        try:
            contexts = await self._container_context_service.resolve_contexts(
                agent_keys=agent_keys,
                runtime_ctx=runtime_ctx,
                tenant_id=actor.tenant_id,
            )
            metadata = self._container_context_service.build_metadata_from_contexts(contexts)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "container_context.resolve.failed",
                extra={"tenant_id": actor.tenant_id, "workflow_run_id": run_id},
                exc_info=exc,
            )

        await self._recorder.start(
            run_id,
            workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
            metadata=metadata,
        )

        if contexts:
            await self._append_container_context_events(
                conversation_id=conversation_id,
                tenant_id=actor.tenant_id,
                contexts=contexts,
                workflow_run_id=run_id,
            )

    async def _append_container_context_events(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        contexts: Mapping[str, dict[str, str | None]],
        workflow_run_id: str,
    ) -> None:
        try:
            events = self._container_context_service.build_run_events_from_contexts(
                contexts,
                response_id=None,
                workflow_run_id=workflow_run_id,
            )
            if not events:
                return
            await self._conversation_service.append_run_events(
                conversation_id,
                tenant_id=tenant_id,
                events=events,
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "container_context.append_failed",
                extra={"tenant_id": tenant_id, "conversation_id": conversation_id},
                exc_info=exc,
            )


class _WorkflowRequestProxy(SimpleNamespace):
    """Tiny adapter so InteractionContextBuilder can reuse its shape expectations."""

    def __init__(
        self,
        *,
        message: str,
        location: Any | None,
        share_location: bool | None,
        container_overrides: dict[str, str] | None = None,
        vector_store_overrides: Mapping[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            location=location,
            share_location=share_location,
            container_overrides=container_overrides,
            vector_store_overrides=vector_store_overrides,
        )


__all__ = ["WorkflowRunBootstrapper", "WorkflowRunContext"]
