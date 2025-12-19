from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.ai import AgentRunResult
from app.domain.ai.models import AgentStreamEvent
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.agents.provider_registry import get_provider_registry
from app.services.containers.files_gateway import ContainerFileContent
from app.services.workflows.runner import WorkflowRunner
from app.workflows._shared.registry import WorkflowRegistry
from app.workflows._shared.specs import WorkflowSpec, WorkflowStep


class _FakeRuntime:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    async def run(self, agent_key: str, message: object, **_: object) -> AgentRunResult:
        self.calls.append((agent_key, message))
        return AgentRunResult(
            final_output="ok",
            response_text="ok",
            response_id="resp_1",
            tool_outputs=[
                {
                    "type": "container_file_citation",
                    "container_id": "cntr_123",
                    "file_id": "cfile_123",
                    "filename": "report.pdf",
                    "start_index": 0,
                    "end_index": 1,
                }
            ],
        )

    def run_stream(self, agent_key: str, message: object, **_: object):
        self.calls.append((agent_key, message))

        class _Stream:
            last_response_id = "resp_1"
            usage = None

            async def events(self):
                yield AgentStreamEvent(
                    kind="raw_response_event",
                    response_id="resp_1",
                    annotations=[
                        {
                            "type": "container_file_citation",
                            "container_id": "cntr_123",
                            "file_id": "cfile_123",
                            "filename": "report.pdf",
                            "start_index": 0,
                            "end_index": 1,
                        }
                    ],
                    is_terminal=False,
                )
                yield AgentStreamEvent(
                    kind="run_item_stream_event",
                    response_id="resp_1",
                    is_terminal=True,
                )

        return _Stream()


def _actor() -> ConversationActorContext:
    return ConversationActorContext(
        tenant_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
    )


def _attachment_service():
    storage = MagicMock()
    storage.put_object = AsyncMock()
    storage.put_object.return_value.id = uuid.uuid4()
    storage.put_object.return_value.checksum_sha256 = "abc"
    storage.put_object.return_value.created_at = None
    storage.get_presigned_download = AsyncMock(return_value=(MagicMock(url="https://u"), MagicMock()))

    gateway = MagicMock()
    gateway.download_file_content = AsyncMock(
        return_value=ContainerFileContent(data=b"%PDF-1.4\n", filename="report.pdf")
    )

    svc = AttachmentService(lambda: storage, container_files_gateway_resolver=lambda: gateway)
    return svc, storage, gateway


@pytest.mark.asyncio
async def test_workflow_run_ingests_container_file_attachments(monkeypatch: pytest.MonkeyPatch):
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

    attachments, storage, gateway = _attachment_service()
    runner = WorkflowRunner(registry=WorkflowRegistry(), attachment_service=attachments)

    spec = WorkflowSpec(
        key="ci-demo",
        display_name="CI Demo",
        description="",
        steps=(WorkflowStep(agent_key="a1"),),
        allow_handoff_agents=True,
    )

    try:
        result = await runner.run(
            spec,
            actor=_actor(),
            message="make a pdf",
            conversation_id="conv",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert result.attachments, "expected attachments to be returned on WorkflowRunResult"
    assert any(att.filename == "report.pdf" for att in result.attachments or [])
    gateway.download_file_content.assert_awaited()
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()


@pytest.mark.asyncio
async def test_workflow_stream_terminal_event_includes_attachments(monkeypatch: pytest.MonkeyPatch):
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

    attachments, storage, gateway = _attachment_service()
    runner = WorkflowRunner(registry=WorkflowRegistry(), attachment_service=attachments)

    spec = WorkflowSpec(
        key="ci-stream-demo",
        display_name="CI Stream Demo",
        description="",
        steps=(WorkflowStep(agent_key="a1"),),
        allow_handoff_agents=True,
    )

    events: list[AgentStreamEvent] = []
    try:
        async for ev in runner.run_stream(
            spec,
            actor=_actor(),
            message="make a pdf",
            conversation_id="conv",
        ):
            events.append(ev)
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert events and events[-1].is_terminal is True
    terminal = events[-1]
    assert terminal.attachments, "expected stored attachment payloads on terminal event"
    assert any(
        isinstance(att, dict) and att.get("filename") == "report.pdf"
        for att in (terminal.attachments or [])
    )
    gateway.download_file_content.assert_awaited()
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()
