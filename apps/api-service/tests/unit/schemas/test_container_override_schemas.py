from __future__ import annotations

from app.api.v1.chat.schemas import AgentChatRequest
from app.api.v1.workflows.schemas import WorkflowRunRequestBody


def test_chat_request_accepts_container_overrides() -> None:
    payload = AgentChatRequest(
        message="hello",
        container_overrides={"triage": "container-uuid"},
    )
    assert payload.container_overrides == {"triage": "container-uuid"}


def test_workflow_request_accepts_container_overrides() -> None:
    payload = WorkflowRunRequestBody(
        message="hello",
        container_overrides={"retriever": "container-uuid"},
    )
    assert payload.container_overrides == {"retriever": "container-uuid"}
