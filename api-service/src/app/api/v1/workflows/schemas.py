from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.utils.tools.location import LocationHint


class WorkflowSummary(BaseModel):
    key: str
    display_name: str
    description: str
    step_count: int
    default: bool = False


class WorkflowRunRequestBody(BaseModel):
    message: str = Field(..., description="Initial user message")
    conversation_id: str | None = Field(
        None, description="Optional conversation id to reuse across steps"
    )
    location: LocationHint | None = Field(
        None, description="Optional coarse location payload for hosted tools"
    )
    share_location: bool | None = Field(
        None, description="If true, forward location to hosted web search"
    )


class WorkflowStepResultSchema(BaseModel):
    name: str
    agent_key: str
    response_text: str | None
    structured_output: Any | None = None
    response_id: str | None = None
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None


class WorkflowRunResponse(BaseModel):
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    steps: list[WorkflowStepResultSchema]
    final_output: Any | None


class StreamingWorkflowEvent(BaseModel):
    kind: Literal[
        "raw_response",
        "run_item",
        "agent_update",
        "usage",
        "error",
        "lifecycle",
    ]
    workflow_key: str
    workflow_run_id: str | None = None
    step_name: str | None = None
    step_agent: str | None = None
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None
    conversation_id: str | None = None
    agent_used: str | None = None
    response_id: str | None = None
    sequence_number: int | None = None
    raw_type: str | None = None
    run_item_name: str | None = None
    run_item_type: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    agent: str | None = None
    new_agent: str | None = None
    text_delta: str | None = None
    reasoning_delta: str | None = None
    response_text: str | None = None
    structured_output: Any | None = None
    is_terminal: bool = False
    payload: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] | None = None


class WorkflowRunDetail(BaseModel):
    workflow_key: str
    workflow_run_id: str
    tenant_id: str
    user_id: str
    status: str
    started_at: str
    ended_at: str | None
    final_output_text: str | None
    final_output_structured: Any | None
    request_message: str | None
    conversation_id: str | None
    steps: list[WorkflowStepResultSchema]
