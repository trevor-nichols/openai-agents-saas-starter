"""Persistence/telemetry adapter for workflow runs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.activity import StatusType
from app.domain.ai import AgentRunResult
from app.domain.workflows import WorkflowRun, WorkflowRunRepository, WorkflowRunStep
from app.services.activity import activity_service
from app.services.agents.context import ConversationActorContext
from app.workflows._shared.specs import WorkflowSpec


def _now():
    import datetime

    return datetime.datetime.now(tz=datetime.UTC)


def _uuid() -> str:
    return str(uuid4())


def _normalize_status(value: str) -> StatusType:
    normalized = value.lower()
    if normalized in {"succeeded", "success"}:
        return "success"
    if normalized in {"failed", "failure", "error", "cancelled", "canceled"}:
        return "failure"
    if normalized in {"pending"}:
        return "pending"
    return "failure"


def _map_activity_action(status: str) -> tuple[str, StatusType, dict[str, object]]:
    normalized = status.lower()
    if normalized in {"cancelled", "canceled"}:
        return "workflow.run.cancelled", "pending", {}
    if normalized in {"succeeded", "success"}:
        return "workflow.run.completed", "success", {"status": status}
    if normalized in {"failed", "failure", "error"}:
        return "workflow.run.completed", "failure", {"status": status}
    # Default: treat unknown as failure
    return "workflow.run.completed", "failure", {"status": status}


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
        metadata: dict[str, Any] | None = None,
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
                metadata=metadata,
                final_output_structured=None,
                final_output_text=None,
                trace_id=None,
                ended_at=None,
            )
        )
        try:
            await activity_service.record(
                tenant_id=actor.tenant_id,
                action="workflow.run.started",
                actor_id=actor.user_id,
                actor_type="user",
                object_type="workflow",
                object_id=workflow.key,
                source="api",
                metadata={
                    "workflow_key": workflow.key,
                    "run_id": run_id,
                    "message": message,
                },
            )
        except Exception:  # pragma: no cover - best effort
            pass

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
        actor: ConversationActorContext,
        workflow_key: str,
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
        try:
            action, activity_status, extra_metadata = _map_activity_action(status)
            await activity_service.record(
                tenant_id=actor.tenant_id,
                action=action,
                actor_id=actor.user_id,
                actor_type="user",
                object_type="workflow_run",
                object_id=run_id,
                status=activity_status,
                source="api",
                metadata={
                    "run_id": run_id,
                    "workflow_key": workflow_key,
                    **extra_metadata,
                },
            )
        except Exception:  # pragma: no cover - best effort
            pass


__all__ = ["WorkflowRunRecorder"]
