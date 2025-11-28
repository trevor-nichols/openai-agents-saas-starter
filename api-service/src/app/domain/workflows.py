from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

WorkflowStatus = Literal["running", "succeeded", "failed"]


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


class WorkflowRunRepository(Protocol):
    async def create_run(self, run: WorkflowRun) -> None: ...

    async def update_run(self, run_id: str, **fields: Any) -> None: ...

    async def create_step(self, step: WorkflowRunStep) -> None: ...

    async def update_step(self, step_id: str, **fields: Any) -> None: ...

    async def get_run_with_steps(
        self, run_id: str
    ) -> tuple[WorkflowRun, list[WorkflowRunStep]]: ...


__all__ = ["WorkflowRun", "WorkflowRunStep", "WorkflowRunRepository", "WorkflowStatus"]
