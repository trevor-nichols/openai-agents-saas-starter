"""Workflow runner that sequences agents deterministically (with optional parallel stages)."""

from __future__ import annotations

import inspect
import logging
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from agents import trace

from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.domain.workflows import WorkflowRunRepository
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.stages import run_parallel_stage, run_sequential_stage
from app.services.workflows.streaming import stream_parallel_stage, stream_sequential_stage
from app.services.workflows.types import WorkflowRunResult, WorkflowStepResult
from app.workflows.registry import WorkflowRegistry
from app.workflows.schema_utils import schema_to_json_schema, validate_against_schema
from app.workflows.specs import WorkflowSpec

logger = logging.getLogger(__name__)


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
    ) -> None:
        self._registry = registry
        self._provider_registry = provider_registry or get_provider_registry()
        self._interaction_builder = interaction_builder or InteractionContextBuilder()
        self._run_repository = run_repository
        self._recorder = WorkflowRunRecorder(run_repository)
        self._cancellations = cancellation_tracker or set()
        self._conversation_service = conversation_service or get_conversation_service()
        self._event_projector = event_projector or EventProjector(self._conversation_service)

    async def _get_session_items(self, session_handle: Any) -> list[dict[str, Any]]:
        getter = getattr(session_handle, "get_items", None)
        if getter is None or not callable(getter):
            return []
        try:
            result = getter()
            items = await result if inspect.isawaitable(result) else result
            if not items:
                return []
            if isinstance(items, list):
                return list(items)
            if isinstance(items, (tuple, set)):  # noqa: UP038 - tuple is runtime-safe for isinstance
                return list(items)
            return []
        except Exception:
            return []

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
            session_items
            if session_items is not None
            else await self._get_session_items(session_handle)
        )
        if not post_items:
            return
        delta = post_items if session_items is not None else post_items[len(pre_items) :]
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

    async def run(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> WorkflowRunResult:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        session_handle = provider.session_store.build(conversation_id)

        await self._conversation_service.append_message(
            conversation_id,
            ConversationMessage(role="user", content=message),
            tenant_id=actor.tenant_id,
            metadata=ConversationMetadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=workflow.key,
                active_agent=_first_agent_key(workflow),
                provider=provider.name,
                user_id=actor.user_id,
            ),
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
        )

        async def session_getter():
            return await self._get_session_items(session_handle)

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

        current_input: Any = message
        steps_results: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()

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

            await self._recorder.end(
                run_id,
                status="succeeded",
                final_output=validated_output,
            )
        except _WorkflowCancelled:
            await self._recorder.end(run_id, status="cancelled", final_output=None)
            raise
        except Exception:
            await self._recorder.end(run_id, status="failed", final_output=None)
            raise

        return WorkflowRunResult(
            workflow_key=workflow.key,
            workflow_run_id=run_id,
            conversation_id=conversation_id,
            steps=steps_results,
            final_output=validated_output if steps_results else None,
            output_schema=schema_to_json_schema(workflow.output_schema),
        )

    async def run_stream(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        session_handle = provider.session_store.build(conversation_id)
        await self._conversation_service.append_message(
            conversation_id,
            ConversationMessage(role="user", content=message),
            tenant_id=actor.tenant_id,
            metadata=ConversationMetadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=workflow.key,
                active_agent=_first_agent_key(workflow),
                provider=provider.name,
                user_id=actor.user_id,
            ),
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
        )

        async def session_getter():
            return await self._get_session_items(session_handle)

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

        current_input: Any = message
        prior_steps: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()

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
                            yield event
                        if prior_steps:
                            current_input = prior_steps[-1].response.final_output

            validated_output = validate_against_schema(
                workflow.output_schema,
                current_input if prior_steps else None,
                label="workflow output",
            )

            await self._recorder.end(
                run_id,
                status="succeeded",
                final_output=validated_output,
            )
        except _WorkflowCancelled:
            await self._recorder.end(run_id, status="cancelled", final_output=None)
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
            await self._recorder.end(run_id, status="failed", final_output=None)
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


__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "WorkflowStepResult",
]
