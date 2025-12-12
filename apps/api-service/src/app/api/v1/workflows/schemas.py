from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.shared.streaming import (
    CodeInterpreterCall,
    ContainerFileCitation,
    FileCitation,
    FileSearchCall,
    MessageAttachment,
    StreamingEvent,
    ToolCallPayload,
    UrlCitation,
    WebSearchAction,
    WebSearchCall,
)
from app.domain.workflows import WorkflowStatus
from app.utils.tools.location import LocationHint


class WorkflowSummary(BaseModel):
    key: str
    display_name: str
    description: str
    step_count: int
    default: bool = False


class WorkflowListResponse(BaseModel):
    """Paginated list of workflows."""

    items: list[WorkflowSummary]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page.",
    )
    total: int = Field(description="Total number of workflows matching the current filter.")


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
    output_schema: dict[str, Any] | None = None


class WorkflowRunResponse(BaseModel):
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    steps: list[WorkflowStepResultSchema]
    final_output: Any | None
    output_schema: dict[str, Any] | None = None


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
    output_schema: dict[str, Any] | None = None
    steps: list[WorkflowStepResultSchema]


class WorkflowRunListItem(BaseModel):
    workflow_run_id: str
    workflow_key: str
    status: WorkflowStatus
    started_at: str
    ended_at: str | None = None
    user_id: str
    conversation_id: str | None = None
    step_count: int
    duration_ms: int | None = None
    final_output_text: str | None = None


class WorkflowRunListResponse(BaseModel):
    items: list[WorkflowRunListItem]
    next_cursor: str | None = None


class WorkflowRunCancelResponse(BaseModel):
    workflow_run_id: str = Field(..., description="The workflow run id that was cancelled.")
    success: bool = Field(..., description="True if the cancel request succeeded.")


class WorkflowStepDescriptor(BaseModel):
    name: str
    agent_key: str
    guard: str | None = None
    guard_type: str | None = None
    input_mapper: str | None = None
    input_mapper_type: str | None = None
    max_turns: int | None = None
    output_schema: dict[str, Any] | None = None


class WorkflowStageDescriptor(BaseModel):
    name: str
    mode: Literal["sequential", "parallel"]
    reducer: str | None = None
    steps: list[WorkflowStepDescriptor]


class WorkflowDescriptorResponse(BaseModel):
    key: str
    display_name: str
    description: str
    default: bool
    allow_handoff_agents: bool
    step_count: int
    stages: list[WorkflowStageDescriptor]
    output_schema: dict[str, Any] | None = None


class StreamingWorkflowEvent(StreamingEvent):
    model_config = ConfigDict(title="StreamingWorkflowEvent")


__all__ = [
    "WorkflowSummary",
    "WorkflowListResponse",
    "WorkflowRunRequestBody",
    "WorkflowRunResponse",
    "WorkflowRunDetail",
    "WorkflowRunListItem",
    "WorkflowRunListResponse",
    "WorkflowRunCancelResponse",
    "WorkflowStepDescriptor",
    "WorkflowStageDescriptor",
    "WorkflowDescriptorResponse",
    "StreamingWorkflowEvent",
    "ToolCallPayload",
    "UrlCitation",
    "ContainerFileCitation",
    "FileCitation",
    "MessageAttachment",
    "WebSearchAction",
    "WebSearchCall",
    "CodeInterpreterCall",
    "FileSearchCall",
]
