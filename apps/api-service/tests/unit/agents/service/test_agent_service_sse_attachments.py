import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.ai.models import AgentStreamEvent
from app.services.agent_service import AgentService
from app.services.agents.context import ConversationActorContext
from app.services.containers.files_gateway import ContainerFileContent


@pytest.mark.asyncio
async def test_sse_events_include_attachments(monkeypatch):
    provider = MagicMock()
    provider.name = "openai"
    provider.resolve_agent.return_value = MagicMock(key="triage", model="gpt-5.1", output_schema=None)

    class MockStream:
        last_response_id = "resp_1"
        usage = None

        async def events(self):
            yield AgentStreamEvent(
                kind="run_item_stream_event",
                response_id="resp_1",
                payload={
                    "type": "image_generation_call",
                    "result": "dGVzdA==",
                    "id": "tc1",
                    "format": "png",
                },
                is_terminal=False,
            )
            yield AgentStreamEvent(kind="run_item_stream_event", response_id="resp_1", is_terminal=True)

    provider.runtime.run_stream.return_value = MockStream()

    storage = MagicMock()
    storage.put_object = AsyncMock()
    storage.put_object.return_value.id = uuid.uuid4()
    storage.put_object.return_value.checksum_sha256 = "abc"
    storage.put_object.return_value.created_at = None
    storage.get_presigned_download = AsyncMock(return_value=(MagicMock(url="https://u"), MagicMock()))

    svc = AgentService(provider_registry=MagicMock(get_default=lambda: provider), storage_service=storage)

    actor = ConversationActorContext(tenant_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))
    req = MagicMock()
    req.agent_type = "triage"
    req.conversation_id = None
    req.message = "hi"
    req.location = None
    req.share_location = False
    req.run_options = None
    req.memory_strategy = None
    req.memory_injection = None

    stream = svc.chat_stream(req, actor=actor)
    events = []
    async for ev in stream:
        events.append(ev)

    assert any(ev.attachments for ev in events)
    assert any(ev.payload and ev.payload.get("_attachment_note") == "stored" for ev in events if ev.payload)
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()


@pytest.mark.asyncio
async def test_sse_terminal_event_includes_container_file_attachments(monkeypatch):
    provider = MagicMock()
    provider.name = "openai"
    provider.resolve_agent.return_value = MagicMock(key="triage", model="gpt-5.1", output_schema=None)

    class MockStream:
        last_response_id = "resp_1"
        usage = None

        async def events(self):
            yield AgentStreamEvent(
                kind="raw_response_event",
                response_id="resp_1",
                raw_type="response.output_text.annotation.added",
                annotations=[
                    {
                        "type": "container_file_citation",
                        "start_index": 0,
                        "end_index": 1,
                        "container_id": "cntr_123",
                        "file_id": "cfile_123",
                        "filename": "squares.csv",
                    }
                ],
                payload={"type": "response.output_text.annotation.added"},
                is_terminal=False,
            )
            yield AgentStreamEvent(kind="run_item_stream_event", response_id="resp_1", is_terminal=True)

    provider.runtime.run_stream.return_value = MockStream()

    storage = MagicMock()
    storage.put_object = AsyncMock()
    storage.put_object.return_value.id = uuid.uuid4()
    storage.put_object.return_value.checksum_sha256 = "abc"
    storage.put_object.return_value.created_at = None
    storage.get_presigned_download = AsyncMock(return_value=(MagicMock(url="https://u"), MagicMock()))

    gateway = MagicMock()
    gateway.download_file_content = AsyncMock(
        return_value=ContainerFileContent(data=b"a,b\n1,2\n", filename="squares.csv")
    )

    svc = AgentService(
        provider_registry=MagicMock(get_default=lambda: provider),
        storage_service=storage,
        container_files_gateway=gateway,
    )

    actor = ConversationActorContext(tenant_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))
    req = MagicMock()
    req.agent_type = "triage"
    req.conversation_id = None
    req.message = "hi"
    req.location = None
    req.share_location = False
    req.run_options = None
    req.memory_strategy = None
    req.memory_injection = None

    events = []
    async for ev in svc.chat_stream(req, actor=actor):
        events.append(ev)

    assert events, "Expected streamed events"
    terminal = events[-1]
    assert terminal.is_terminal is True
    assert terminal.attachments, "Expected stored attachment payloads on terminal event"
    assert any(att.get("filename") == "squares.csv" for att in terminal.attachments if isinstance(att, dict))

    gateway.download_file_content.assert_awaited()
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()
