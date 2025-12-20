"""Workflow runner that sequences agents deterministically (with optional parallel stages)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any, cast

from agents import trace

from app.api.v1.shared.attachments import InputAttachment
from app.domain.ai.models import AgentStreamEvent
from app.domain.workflows import WorkflowRunRepository
from app.services.agents.attachments import AttachmentService
from app.services.agents.container_context import ContainerContextService
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.input_attachments import InputAttachmentService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import (
    AgentProviderRegistry,
    get_provider_registry,
)
from app.services.assets.service import AssetService
from app.services.containers import ContainerService
from app.services.conversation_service import (
    ConversationService,
    get_conversation_service,
)
from app.services.workflows.attachments import WorkflowAttachmentCollector
from app.services.workflows.output import (
    WorkflowAssistantMessageWriter,
    aggregate_usage,
    format_stream_output,
    render_workflow_output_text,
)
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.run_context import WorkflowRunBootstrapper
from app.services.workflows.session_events import SessionDeltaProjector
from app.services.workflows.stages import run_parallel_stage, run_sequential_stage
from app.services.workflows.streaming import stream_parallel_stage, stream_sequential_stage
from app.services.workflows.types import WorkflowRunResult, WorkflowStepResult
from app.services.workflows.utils import first_agent_key
from app.workflows._shared.registry import WorkflowRegistry
from app.workflows._shared.schema_utils import schema_to_json_schema, validate_against_schema
from app.workflows._shared.specs import WorkflowSpec


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
        container_service: ContainerService | None = None,
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
        self._asset_service = asset_service
        self._bootstrapper = WorkflowRunBootstrapper(
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            recorder=self._recorder,
            container_context_service=ContainerContextService(
                container_service=container_service
            ),
            input_attachment_service=input_attachment_service,
            asset_service=asset_service,
        )
        self._message_writer = WorkflowAssistantMessageWriter(
            conversation_service=self._conversation_service,
            asset_service=asset_service,
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
        container_overrides: dict[str, str] | None = None,
        vector_store_overrides: Mapping[str, Any] | None = None,
    ) -> WorkflowRunResult:
        ctx = await self._bootstrapper.prepare(
            workflow,
            actor=actor,
            message=message,
            attachments=attachments,
            conversation_id=conversation_id,
            location=location,
            share_location=share_location,
            container_overrides=container_overrides,
            vector_store_overrides=vector_store_overrides,
        )
        session_projector = SessionDeltaProjector(
            event_projector=self._event_projector,
            conversation_id=conversation_id,
            tenant_id=actor.tenant_id,
            workflow_run_id=ctx.run_id,
            session_handle=ctx.session_handle,
        )

        current_input: Any = ctx.agent_input
        steps_results: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()
        collector = (
            WorkflowAttachmentCollector(
                attachment_service=self._attachment_service,
                actor=actor,
                conversation_id=conversation_id,
            )
            if self._attachment_service is not None
            else None
        )

        def _check_cancel() -> None:
            self._raise_if_cancelled(ctx.run_id)

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    _check_cancel()
                    if stage.mode == "parallel":
                        current_input = await run_parallel_stage(
                            run_id=ctx.run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            steps_results=steps_results,
                            provider=ctx.provider,
                            runtime_ctx=ctx.runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_projector.get_session_items,
                            ingest_session_delta=session_projector.ingest_delta,
                            session_handle=ctx.session_handle,
                            workflow_run_id=ctx.run_id,
                        )
                    else:
                        current_input = await run_sequential_stage(
                            run_id=ctx.run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            steps_results=steps_results,
                            provider=ctx.provider,
                            runtime_ctx=ctx.runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_projector.get_session_items,
                            ingest_session_delta=session_projector.ingest_delta,
                            session_handle=ctx.session_handle,
                        )

            validated_output = validate_against_schema(
                workflow.output_schema,
                current_input if steps_results else None,
                label="workflow output",
            )

            if collector and steps_results:
                await collector.ingest_step_outputs(steps_results)

            output_attachments = collector.attachments if collector else []
            await self._message_writer.write(
                workflow=workflow,
                actor=actor,
                provider_name=ctx.provider.name,
                conversation_id=conversation_id,
                response_text=render_workflow_output_text(validated_output),
                attachments=output_attachments,
                active_agent=(steps_results[-1].agent_key if steps_results else None),
            )

            await self._recorder.end(
                ctx.run_id,
                status="succeeded",
                final_output=validated_output,
                actor=actor,
                workflow_key=workflow.key,
            )
        except _WorkflowCancelled:
            await self._recorder.end(
                ctx.run_id,
                status="cancelled",
                final_output=None,
                actor=actor,
                workflow_key=workflow.key,
            )
            raise
        except Exception:
            await self._recorder.end(
                ctx.run_id,
                status="failed",
                final_output=None,
                actor=actor,
                workflow_key=workflow.key,
            )
            raise

        return WorkflowRunResult(
            workflow_key=workflow.key,
            workflow_run_id=ctx.run_id,
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
        container_overrides: dict[str, str] | None = None,
        vector_store_overrides: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        ctx = await self._bootstrapper.prepare(
            workflow,
            actor=actor,
            message=message,
            attachments=attachments,
            conversation_id=conversation_id,
            location=location,
            share_location=share_location,
            container_overrides=container_overrides,
            vector_store_overrides=vector_store_overrides,
        )
        session_projector = SessionDeltaProjector(
            event_projector=self._event_projector,
            conversation_id=conversation_id,
            tenant_id=actor.tenant_id,
            workflow_run_id=ctx.run_id,
            session_handle=ctx.session_handle,
        )

        current_input: Any = ctx.agent_input
        prior_steps: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()
        collector = (
            WorkflowAttachmentCollector(
                attachment_service=self._attachment_service,
                actor=actor,
                conversation_id=conversation_id,
            )
            if self._attachment_service is not None
            else None
        )

        def _check_cancel() -> None:
            self._raise_if_cancelled(ctx.run_id)

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    _check_cancel()
                    if stage.mode == "parallel":
                        stage_state: dict[str, Any] = {}
                        async for event in stream_parallel_stage(
                            run_id=ctx.run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            prior_steps=prior_steps,
                            provider=ctx.provider,
                            runtime_ctx=ctx.runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            stage_state=stage_state,
                            session_getter=session_projector.get_session_items,
                            ingest_session_delta=session_projector.ingest_delta,
                            session_handle=ctx.session_handle,
                            workflow_run_id=ctx.run_id,
                        ):
                            if collector is not None:
                                await collector.ingest_stream_event(event)
                            yield event
                        current_input = stage_state.get(
                            "next_input",
                            prior_steps[-1].response.final_output if prior_steps else current_input,
                        )
                    else:
                        _check_cancel()
                        async for event in stream_sequential_stage(
                            run_id=ctx.run_id,
                            workflow=workflow,
                            stage=stage,
                            current_input=current_input,
                            prior_steps=prior_steps,
                            provider=ctx.provider,
                            runtime_ctx=ctx.runtime_ctx,
                            conversation_id=conversation_id,
                            recorder=self._recorder,
                            check_cancel=_check_cancel,
                            session_getter=session_projector.get_session_items,
                            ingest_session_delta=session_projector.ingest_delta,
                            session_handle=ctx.session_handle,
                        ):
                            if collector is not None:
                                await collector.ingest_stream_event(event)
                            yield event
                        if prior_steps:
                            current_input = prior_steps[-1].response.final_output

            validated_output = validate_against_schema(
                workflow.output_schema,
                current_input if prior_steps else None,
                label="workflow output",
            )

            if collector is not None:
                await collector.finalize_stream_container_citations(
                    fallback_agent_key=prior_steps[-1].agent_key if prior_steps else None
                )

            output_attachments = collector.attachments if collector else []
            await self._message_writer.write(
                workflow=workflow,
                actor=actor,
                provider_name=ctx.provider.name,
                conversation_id=conversation_id,
                response_text=render_workflow_output_text(validated_output),
                attachments=output_attachments,
                active_agent=(prior_steps[-1].agent_key if prior_steps else None),
            )

            await self._recorder.end(
                ctx.run_id,
                status="succeeded",
                final_output=validated_output,
                actor=actor,
                workflow_key=workflow.key,
            )

            last_step = prior_steps[-1] if prior_steps else None
            response_text, structured_output = format_stream_output(validated_output)

            yield AgentStreamEvent(
                kind="run_item_stream_event",
                conversation_id=conversation_id,
                response_id=last_step.response.response_id if last_step else None,
                agent=last_step.agent_key if last_step else first_agent_key(workflow),
                is_terminal=True,
                response_text=response_text,
                structured_output=structured_output,
                usage=aggregate_usage([step.response.usage for step in prior_steps]),
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
                    "workflow_run_id": ctx.run_id,
                    "step_name": last_step.name if last_step else None,
                    "step_agent": last_step.agent_key if last_step else None,
                    "stage_name": last_step.stage_name if last_step else None,
                    "parallel_group": last_step.parallel_group if last_step else None,
                    "branch_index": last_step.branch_index if last_step else None,
                },
            )
        except _WorkflowCancelled:
            await self._recorder.end(
                ctx.run_id,
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
                    "workflow_run_id": ctx.run_id,
                    "state": "cancelled",
                },
            )
        except Exception:
            await self._recorder.end(
                ctx.run_id,
                status="failed",
                final_output=None,
                actor=actor,
                workflow_key=workflow.key,
            )
            raise

    def flag_cancel(self, run_id: str) -> None:
        self._cancellations.add(run_id)

    def _raise_if_cancelled(self, run_id: str) -> None:
        if run_id in self._cancellations:
            raise _WorkflowCancelled()


class _WorkflowCancelled(Exception):
    """Internal marker exception for cooperative cancellation."""


__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "WorkflowStepResult",
]
