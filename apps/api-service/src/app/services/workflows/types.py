"""Shared dataclasses used by workflow runner helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.ai import AgentRunResult
from app.domain.conversations import ConversationAttachment


@dataclass(slots=True)
class WorkflowStepResult:
    name: str
    agent_key: str
    response: AgentRunResult
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None
    output_schema: dict[str, Any] | None = None


@dataclass(slots=True)
class WorkflowRunResult:
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    steps: list[WorkflowStepResult]
    final_output: Any | None = None
    output_schema: dict[str, Any] | None = None
    attachments: list[ConversationAttachment] | None = None


__all__ = ["WorkflowStepResult", "WorkflowRunResult"]
