from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

WorkflowStatus = Literal["running", "succeeded", "failed", "cancelled"]


@dataclass(slots=True)
class WorkflowRun:
    id: str
    workflow_key: str
    tenant_id: str
    user_id: str
    status: WorkflowStatus
    started_at: datetime
    ended_at: datetime | None = None
    final_output_text: str | None = None
    final_output_structured: Any | None = None
    trace_id: str | None = None
    request_message: str | None = None
    conversation_id: str | None = None
    metadata: dict[str, Any] | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    deleted_reason: str | None = None


@dataclass(slots=True)
class WorkflowRunStep:
    id: str
    workflow_run_id: str
    sequence_no: int
    step_name: str
    step_agent: str
    status: WorkflowStatus
    started_at: datetime
    ended_at: datetime | None = None
    response_id: str | None = None
    response_text: str | None = None
    structured_output: Any | None = None
    raw_payload: dict[str, Any] | None = None
    usage_input_tokens: int | None = None
    usage_output_tokens: int | None = None
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    deleted_reason: str | None = None


class WorkflowRunRepository(Protocol):
    async def create_run(self, run: WorkflowRun) -> None: ...

    async def update_run(self, run_id: str, **fields: Any) -> None: ...

    async def create_step(self, step: WorkflowRunStep) -> None: ...

    async def update_step(self, step_id: str, **fields: Any) -> None: ...

    async def get_run_with_steps(
        self, run_id: str, *, include_deleted: bool = False
    ) -> tuple[WorkflowRun, list[WorkflowRunStep]]: ...

    async def list_runs(
        self,
        *,
        tenant_id: str,
        workflow_key: str | None = None,
        status: WorkflowStatus | None = None,
        started_before: datetime | None = None,
        started_after: datetime | None = None,
        conversation_id: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> WorkflowRunListPage: ...

    async def cancel_run(self, run_id: str, *, ended_at: datetime) -> None: ...

    async def cancel_running_steps(self, run_id: str, *, ended_at: datetime) -> None: ...

    async def soft_delete_run(
        self, run_id: str, *, tenant_id: str, deleted_by: str, reason: str | None = None
    ) -> None: ...

    async def hard_delete_run(self, run_id: str, *, tenant_id: str) -> None: ...


@dataclass(slots=True)
class WorkflowRunListItem:
    id: str
    workflow_key: str
    status: WorkflowStatus
    started_at: datetime
    ended_at: datetime | None
    user_id: str
    conversation_id: str | None
    step_count: int
    duration_ms: int | None
    final_output_text: str | None


@dataclass(slots=True)
class WorkflowRunListPage:
    items: list[WorkflowRunListItem]
    next_cursor: str | None


__all__ = [
    "WorkflowRun",
    "WorkflowRunStep",
    "WorkflowRunRepository",
    "WorkflowStatus",
    "WorkflowRunListItem",
    "WorkflowRunListPage",
]
