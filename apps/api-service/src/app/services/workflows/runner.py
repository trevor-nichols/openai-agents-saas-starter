"""Workflow runner that sequences agents deterministically (with optional parallel stages)."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator, Mapping
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from agents import trace

from app.api.v1.shared.attachments import InputAttachment
from app.domain.ai.models import AgentRunUsage, AgentStreamEvent
from app.domain.conversations import (
    ConversationAttachment,
    ConversationMessage,
    ConversationMetadata,
)
from app.domain.input_attachments import InputAttachmentRef
from app.domain.workflows import WorkflowRunRepository
from app.services.agents.attachment_utils import collect_container_file_citations_from_event
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.input_attachments import InputAttachmentService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.services.agents.session_items import compute_session_delta, get_session_items
from app.services.assets.service import AssetService
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.stages import run_parallel_stage, run_sequential_stage
from app.services.workflows.streaming import stream_parallel_stage, stream_sequential_stage
from app.services.workflows.types import WorkflowRunResult, WorkflowStepResult
from app.workflows._shared.registry import WorkflowRegistry
from app.workflows._shared.schema_utils import schema_to_json_schema, validate_against_schema
from app.workflows._shared.specs import WorkflowSpec

logger = logging.getLogger(__name__)


def _aggregate_usage(usages: list[AgentRunUsage | None]) -> AgentRunUsage | None:
    totals: dict[str, int] = {}
    saw_any = False
    for usage in usages:
        if usage is None:
            continue
        for field_name in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cached_input_tokens",
            "reasoning_output_tokens",
            "requests",
        ):
            value = getattr(usage, field_name, None)
            if isinstance(value, int):
                totals[field_name] = totals.get(field_name, 0) + value
                saw_any = True
    if not saw_any:
        return None
    return AgentRunUsage(
        input_tokens=totals.get("input_tokens"),
        output_tokens=totals.get("output_tokens"),
        total_tokens=totals.get("total_tokens"),
        cached_input_tokens=totals.get("cached_input_tokens"),
        reasoning_output_tokens=totals.get("reasoning_output_tokens"),
        requests=totals.get("requests"),
    )


class WorkflowRunner:
    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        provider_registry: AgentProviderRegistry | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        run_repository: WorkflowRunRepository | None = None,
        cancellation_tracker: set[str] | None = None,
        conversation_service: ConversationService | None = None,
        event_projector: EventProjector | None = None,
        attachment_service: AttachmentService | None = None,
        input_attachment_service: InputAttachmentService | None = None,
        asset_service: AssetService | None = None,
    ) -> None:
        self._registry = registry
        self._provider_registry = provider_registry or get_provider_registry()
        self._interaction_builder = interaction_builder or InteractionContextBuilder()
        self._run_repository = run_repository
        self._recorder = WorkflowRunRecorder(run_repository)
        self._cancellations = cancellation_tracker or set()
        self._conversation_service = conversation_service or get_conversation_service()
        self._event_projector = event_projector or EventProjector(self._conversation_service)
        self._attachment_service = attachment_service
        self._input_attachment_service = input_attachment_service
        self._asset_service = asset_service

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

    async def _ingest_session_delta(
        self,
        *,
        session_handle: Any,
        pre_items: list[dict[str, Any]],
        conversation_id: str,
        tenant_id: str,
        agent: str | None,
        model: str | None,
        response_id: str | None,
        workflow_run_id: str,
        session_items: list[dict[str, Any]] | None = None,
    ) -> None:
        post_items = (
            session_items if session_items is not None else await get_session_items(session_handle)
        )
        if not post_items:
            return
        delta = (
            post_items
            if session_items is not None
            else compute_session_delta(pre_items, post_items)
        )
        if not delta:
            return
        try:
            await self._event_projector.ingest_session_items(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                session_items=delta,
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=workflow_run_id,
            )
        except Exception:
            logger.exception(
                "workflow_event_projection_failed",
                extra={
                    "conversation_id": conversation_id,
                    "workflow_run_id": workflow_run_id,
                    "agent": agent,
                },
            )

    async def _persist_workflow_assistant_message(
        self,
        *,
        workflow: WorkflowSpec,
        actor: ConversationActorContext,
        provider_name: str | None,
        conversation_id: str,
        response_text: str,
        attachments: list[ConversationAttachment],
        active_agent: str | None,
    ) -> None:
        """Persist the workflow result as a single assistant message (chat parity)."""

        message_id = await self._conversation_service.append_message(
            conversation_id,
            ConversationMessage(role="assistant", content=response_text, attachments=attachments),
            tenant_id=actor.tenant_id,
            metadata=ConversationMetadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=workflow.key,
                active_agent=active_agent,
                provider=provider_name,
                user_id=actor.user_id,
            ),
        )
        if self._asset_service and message_id is not None and attachments:
            try:
                storage_ids = [uuid.UUID(att.object_id) for att in attachments]
            except Exception:
                logger.warning(
                    "asset.link_failed_invalid_object_ids",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                    },
                )
                return
            try:
                await self._asset_service.link_assets_to_message(
                    tenant_id=uuid.UUID(actor.tenant_id),
                    message_id=message_id,
                    storage_object_ids=storage_ids,
                )
            except Exception as exc:
                logger.warning(
                    "asset.link_failed",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                    },
                    exc_info=exc,
                )

    async def run(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        attachments: list[InputAttachment] | None,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> WorkflowRunResult:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        entry_agent = _first_agent_key(workflow) or workflow.key
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
        await self._recorder.start(
            run_id,
            workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
        )
        runtime_ctx = await self._interaction_builder.build(
            actor=actor,
            request=_WorkflowRequestProxy(
                message=message,
                location=location,
                share_location=share_location,
            ),
            conversation_id=conversation_id,
            agent_keys=_workflow_agent_keys(workflow),
        )

        async def session_getter():
            return await get_session_items(session_handle)

        async def ingest_session_delta(
            *,
            pre_items: list[dict[str, Any]],
            agent: str | None,
            model: str | None,
            response_id: str | None,
            session_items: list[dict[str, Any]] | None = None,
        ):
            await self._ingest_session_delta(
                session_handle=session_handle,
                pre_items=pre_items,
                conversation_id=conversation_id,
                tenant_id=actor.tenant_id,
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=run_id,
                session_items=session_items,
            )

        current_input: Any = agent_input
        steps_results: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()
        output_attachments: list[ConversationAttachment] = []
        seen_tool_calls: set[str] = set()
        seen_container_files: set[str] = set()

        def _check_cancel() -> None:
            self._raise_if_cancelled(run_id)

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    _check_cancel()
                    if stage.mode == "parallel":
                        current_input = await run_parallel_stage(
                            run_id=run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            steps_results=steps_results,
                            provider=provider,
                            runtime_ctx=runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_getter,
                            ingest_session_delta=ingest_session_delta,
                            session_handle=session_handle,
                            workflow_run_id=run_id,
                        )
                    else:
                        current_input = await run_sequential_stage(
                            run_id=run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            steps_results=steps_results,
                            provider=provider,
                            runtime_ctx=runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_getter,
                            ingest_session_delta=ingest_session_delta,
                            session_handle=session_handle,
                        )

            validated_output = validate_against_schema(
                workflow.output_schema,
                current_input if steps_results else None,
                label="workflow output",
            )

            if self._attachment_service is not None and steps_results:
                ingest_container_files = self._attachment_service.ingest_container_file_citations
                for step in steps_results:
                    tool_outputs = getattr(step.response, "tool_outputs", None)
                    if not tool_outputs:
                        continue
                    images = await self._attachment_service.ingest_image_outputs(
                        tool_outputs,
                        actor=actor,
                        conversation_id=conversation_id,
                        agent_key=step.agent_key,
                        response_id=step.response.response_id,
                        seen_tool_calls=seen_tool_calls,
                    )
                    if images:
                        output_attachments.extend(images)

                    container_files = await ingest_container_files(
                        tool_outputs,
                        actor=actor,
                        conversation_id=conversation_id,
                        agent_key=step.agent_key,
                        response_id=step.response.response_id,
                        seen_citations=seen_container_files,
                    )
                    if container_files:
                        output_attachments.extend(container_files)

            await self._persist_workflow_assistant_message(
                workflow=workflow,
                actor=actor,
                provider_name=provider.name,
                conversation_id=conversation_id,
                response_text=_render_workflow_output_text(validated_output),
                attachments=output_attachments,
                active_agent=(steps_results[-1].agent_key if steps_results else None),
            )

            await self._recorder.end(
                run_id,
                status="succeeded",
                final_output=validated_output,
                actor=actor,
                workflow_key=workflow.key,
            )
        except _WorkflowCancelled:
            await self._recorder.end(
                run_id,
                status="cancelled",
                final_output=None,
                actor=actor,
                workflow_key=workflow.key,
            )
            raise
        except Exception:
            await self._recorder.end(
                run_id, status="failed", final_output=None, actor=actor, workflow_key=workflow.key
            )
            raise

        return WorkflowRunResult(
            workflow_key=workflow.key,
            workflow_run_id=run_id,
            conversation_id=conversation_id,
            steps=steps_results,
            final_output=validated_output if steps_results else None,
            output_schema=schema_to_json_schema(workflow.output_schema),
            attachments=output_attachments,
        )

    async def run_stream(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        attachments: list[InputAttachment] | None,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        entry_agent = _first_agent_key(workflow) or workflow.key
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
        await self._recorder.start(
            run_id,
            workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
        )
        runtime_ctx = await self._interaction_builder.build(
            actor=actor,
            request=_WorkflowRequestProxy(
                message=message,
                location=location,
                share_location=share_location,
            ),
            conversation_id=conversation_id,
            agent_keys=_workflow_agent_keys(workflow),
        )

        async def session_getter():
            return await get_session_items(session_handle)

        async def ingest_session_delta(
            *,
            pre_items: list[dict[str, Any]],
            agent: str | None,
            model: str | None,
            response_id: str | None,
            session_items: list[dict[str, Any]] | None = None,
        ):
            await self._ingest_session_delta(
                session_handle=session_handle,
                pre_items=pre_items,
                conversation_id=conversation_id,
                tenant_id=actor.tenant_id,
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=run_id,
                session_items=session_items,
            )

        current_input: Any = agent_input
        prior_steps: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()
        output_attachments: list[ConversationAttachment] = []
        seen_tool_calls: set[str] = set()
        pending_container_citations: list[tuple[Mapping[str, Any], str | None, str | None]] = []
        seen_container_files: set[str] = set()

        def _check_cancel() -> None:
            self._raise_if_cancelled(run_id)

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    _check_cancel()
                    if stage.mode == "parallel":
                        stage_state: dict[str, Any] = {}
                        async for event in stream_parallel_stage(
                            run_id=run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            prior_steps=prior_steps,
                            provider=provider,
                            runtime_ctx=runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            stage_state=stage_state,
                            session_getter=session_getter,
                            ingest_session_delta=ingest_session_delta,
                            session_handle=session_handle,
                            workflow_run_id=run_id,
                        ):
                            if self._attachment_service is not None:
                                await _maybe_ingest_workflow_event_attachments(
                                    event=event,
                                    attachment_service=self._attachment_service,
                                    actor=actor,
                                    conversation_id=conversation_id,
                                    attachments_out=output_attachments,
                                    seen_tool_calls=seen_tool_calls,
                                    pending_container_citations=pending_container_citations,
                                    seen_container_files=seen_container_files,
                                )
                            yield event
                        current_input = stage_state.get(
                            "next_input",
                            prior_steps[-1].response.final_output if prior_steps else current_input,
                        )
                    else:
                        _check_cancel()
                        async for event in stream_sequential_stage(
                            run_id=run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            prior_steps=prior_steps,
                            provider=provider,
                            runtime_ctx=runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_getter,
                            ingest_session_delta=ingest_session_delta,
                            session_handle=session_handle,
                        ):
                            if self._attachment_service is not None:
                                await _maybe_ingest_workflow_event_attachments(
                                    event=event,
                                    attachment_service=self._attachment_service,
                                    actor=actor,
                                    conversation_id=conversation_id,
                                    attachments_out=output_attachments,
                                    seen_tool_calls=seen_tool_calls,
                                    pending_container_citations=pending_container_citations,
                                    seen_container_files=seen_container_files,
                                )
                            yield event
                        if prior_steps:
                            current_input = prior_steps[-1].response.final_output

            validated_output = validate_against_schema(
                workflow.output_schema,
                current_input if prior_steps else None,
                label="workflow output",
            )

            if self._attachment_service is not None and pending_container_citations:
                ingest_container_files = self._attachment_service.ingest_container_file_citations
                grouped: dict[str, list[tuple[Mapping[str, Any], str | None]]] = {}
                for citation, agent_key, response_id in pending_container_citations:
                    grouped.setdefault(agent_key or "", []).append((citation, response_id))
                for agent_key, items in grouped.items():
                    citations = [c for c, _ in items]
                    response_id = next((rid for _, rid in items if rid), None)
                    container_files = await ingest_container_files(
                        citations,
                        actor=actor,
                        conversation_id=conversation_id,
                        agent_key=agent_key or (prior_steps[-1].agent_key if prior_steps else ""),
                        response_id=response_id,
                    )
                    if container_files:
                        output_attachments.extend(container_files)

            await self._persist_workflow_assistant_message(
                workflow=workflow,
                actor=actor,
                provider_name=provider.name,
                conversation_id=conversation_id,
                response_text=_render_workflow_output_text(validated_output),
                attachments=output_attachments,
                active_agent=(prior_steps[-1].agent_key if prior_steps else None),
            )

            await self._recorder.end(
                run_id,
                status="succeeded",
                final_output=validated_output,
                actor=actor,
                workflow_key=workflow.key,
            )

            last_step = prior_steps[-1] if prior_steps else None
            response_text: str | None = None
            structured_output: Any | None = None
            if validated_output is not None:
                if isinstance(validated_output, str):
                    response_text = validated_output
                else:
                    structured_output = validated_output
                    try:
                        response_text = json.dumps(validated_output, ensure_ascii=False)
                    except Exception:  # pragma: no cover - defensive
                        response_text = str(validated_output)

            yield AgentStreamEvent(
                kind="run_item_stream_event",
                conversation_id=conversation_id,
                response_id=last_step.response.response_id if last_step else None,
                agent=last_step.agent_key if last_step else _first_agent_key(workflow),
                is_terminal=True,
                response_text=response_text,
                structured_output=structured_output,
                usage=_aggregate_usage([step.response.usage for step in prior_steps]),
                attachments=(
                    [
                        cast(
                            Mapping[str, Any],
                            self._attachment_service.to_attachment_payload(att),
                        )
                        for att in output_attachments
                    ]
                    if self._attachment_service is not None
                    else None
                ),
                metadata={
                    "workflow_key": workflow.key,
                    "workflow_run_id": run_id,
                    "step_name": last_step.name if last_step else None,
                    "step_agent": last_step.agent_key if last_step else None,
                    "stage_name": last_step.stage_name if last_step else None,
                    "parallel_group": last_step.parallel_group if last_step else None,
                    "branch_index": last_step.branch_index if last_step else None,
                },
            )
        except _WorkflowCancelled:
            await self._recorder.end(
                run_id,
                status="cancelled",
                final_output=None,
                actor=actor,
                workflow_key=workflow.key,
            )
            # Emit terminal lifecycle event so stream consumers learn about cancellation.
            yield AgentStreamEvent(
                kind="lifecycle",
                is_terminal=True,
                metadata={
                    "workflow_key": workflow.key,
                    "workflow_run_id": run_id,
                    "state": "cancelled",
                },
            )
        except Exception:
            await self._recorder.end(
                run_id, status="failed", final_output=None, actor=actor, workflow_key=workflow.key
            )
            raise

    def flag_cancel(self, run_id: str) -> None:
        self._cancellations.add(run_id)

    def _raise_if_cancelled(self, run_id: str) -> None:
        if run_id in self._cancellations:
            raise _WorkflowCancelled()


def _uuid() -> str:
    return str(uuid4())


class _WorkflowRequestProxy(SimpleNamespace):
    """Tiny adapter so InteractionContextBuilder can reuse its shape expectations."""

    def __init__(self, *, message: str, location: Any | None, share_location: bool | None):
        super().__init__(message=message, location=location, share_location=share_location)


class _WorkflowCancelled(Exception):
    """Internal marker exception for cooperative cancellation."""


def _first_agent_key(workflow: WorkflowSpec) -> str | None:
    for stage in workflow.resolved_stages():
        for step in stage.steps:
            return step.agent_key
    return None


def _workflow_agent_keys(workflow: WorkflowSpec) -> list[str]:
    seen: set[str] = set()
    for stage in workflow.resolved_stages():
        for step in stage.steps:
            seen.add(step.agent_key)
    return list(seen)


def _render_workflow_output_text(value: Any) -> str:
    """Best-effort conversion of a workflow output into message text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:  # pragma: no cover - defensive
        return str(value)


async def _maybe_ingest_workflow_event_attachments(
    *,
    event: AgentStreamEvent,
    attachment_service: AttachmentService,
    actor: ConversationActorContext,
    conversation_id: str,
    attachments_out: list[ConversationAttachment],
    seen_tool_calls: set[str],
    pending_container_citations: list[tuple[Mapping[str, Any], str | None, str | None]],
    seen_container_files: set[str],
) -> None:
    """Ingest any attachments discoverable from a workflow stream event.

    - Images are ingested opportunistically from payload/tool_call mappings.
    - Code Interpreter container file citations are collected and ingested after
      the workflow completes (to align persistence with the terminal event).
    """

    new_citations = collect_container_file_citations_from_event(event, seen=seen_container_files)
    for ann in new_citations:
        pending_container_citations.append(
            (dict(ann), event.step_agent or event.agent, event.response_id)
        )

    attachment_sources: list[Mapping[str, Any]] = []
    if isinstance(event.payload, Mapping):
        attachment_sources.append(event.payload)
    if isinstance(event.tool_call, Mapping):
        attachment_sources.append(event.tool_call)
    if not attachment_sources:
        return

    agent_key = event.step_agent or event.agent
    if not agent_key:
        return

    images = await attachment_service.ingest_image_outputs(
        attachment_sources,
        actor=actor,
        conversation_id=conversation_id,
        agent_key=str(agent_key),
        response_id=event.response_id,
        seen_tool_calls=seen_tool_calls,
    )
    if not images:
        return

    attachments_out.extend(images)
    payloads: list[Mapping[str, Any]] = [
        cast(Mapping[str, Any], attachment_service.to_attachment_payload(att)) for att in images
    ]
    if event.attachments is None:
        event.attachments = payloads
    else:
        event.attachments.extend(payloads)


__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "WorkflowStepResult",
]
