import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.ai.models import AgentStreamEvent
from app.services.agent_service import AgentService
from app.services.agents.context import ConversationActorContext


@pytest.mark.asyncio
async def test_sse_events_include_attachments(monkeypatch):
    provider = MagicMock()
    provider.name = "openai"
    provider.resolve_agent.return_value = MagicMock(key="triage", model="gpt-5.1")

    class MockStream:
        last_response_id = "resp_1"
        usage = None

        async def events(self):
            yield AgentStreamEvent(
                kind="run_item",
                response_id="resp_1",
                payload={
                    "type": "image_generation_call",
                    "result": "dGVzdA==",
                    "id": "tc1",
                    "format": "png",
                },
                is_terminal=False,
            )
            yield AgentStreamEvent(kind="run_item", response_id="resp_1", is_terminal=True)

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

    stream = svc.chat_stream(req, actor=actor)
    events = []
    async for ev in stream:
        events.append(ev)

    assert any(ev.attachments for ev in events)
    assert any(ev.payload and ev.payload.get("_attachment_note") == "stored" for ev in events if ev.payload)
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()
