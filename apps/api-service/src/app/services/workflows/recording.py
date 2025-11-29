"""Persistence/telemetry adapter for workflow runs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.ai import AgentRunResult
from app.domain.workflows import WorkflowRun, WorkflowRunRepository, WorkflowRunStep
from app.services.agents.context import ConversationActorContext
from app.workflows.specs import WorkflowSpec


def _now():
    import datetime

    return datetime.datetime.now(tz=datetime.UTC)


def _uuid() -> str:
    return str(uuid4())


class WorkflowRunRecorder:
    """Records workflow run + step lifecycle events via the repository if provided."""

    def __init__(self, repository: WorkflowRunRepository | None) -> None:
        self._repository = repository

    async def start(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
    ) -> None:
        if not self._repository:
            return
        await self._repository.create_run(
            WorkflowRun(
                id=run_id,
                workflow_key=workflow.key,
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                status="running",
                started_at=_now(),
                request_message=message,
                conversation_id=conversation_id,
                metadata=None,
                final_output_structured=None,
                final_output_text=None,
                trace_id=None,
                ended_at=None,
            )
        )

    async def step_end(
        self,
        run_id: str,
        *,
        sequence_no: int,
        step_name: str,
        step_agent: str,
        response: AgentRunResult,
        status: str,
        stage_name: str | None,
        parallel_group: str | None,
        branch_index: int | None,
    ) -> None:
        if not self._repository:
            return

        raw_payload = response.metadata if isinstance(response.metadata, dict) else None
        await self._repository.create_step(
            WorkflowRunStep(
                id=_uuid(),
                workflow_run_id=run_id,
                sequence_no=sequence_no,
                step_name=step_name,
                step_agent=step_agent,
                status=status,  # type: ignore[arg-type]
                started_at=_now(),
                ended_at=_now(),
                response_id=response.response_id,
                response_text=response.response_text,
                structured_output=response.structured_output,
                raw_payload=raw_payload,
                usage_input_tokens=getattr(response.usage, "input_tokens", None),
                usage_output_tokens=getattr(response.usage, "output_tokens", None),
                stage_name=stage_name,
                parallel_group=parallel_group,
                branch_index=branch_index,
            )
        )

    async def end(
        self,
        run_id: str,
        *,
        status: str,
        final_output: Any,
    ) -> None:
        if not self._repository:
            return

        await self._repository.update_run(
            run_id,
            status=status,
            ended_at=_now(),
            final_output_text=str(final_output) if final_output is not None else None,
            final_output_structured=final_output if not isinstance(final_output, str) else None,
        )


__all__ = ["WorkflowRunRecorder"]
