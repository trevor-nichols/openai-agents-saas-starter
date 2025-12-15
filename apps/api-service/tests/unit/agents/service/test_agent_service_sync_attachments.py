import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.agent_service import AgentService
from app.services.agents.context import ConversationActorContext
from app.domain.ai.models import AgentRunResult


@pytest.mark.asyncio
async def test_sync_chat_ingests_tool_call_item_images(monkeypatch):
    provider = MagicMock()
    provider.name = "openai"
    provider.resolve_agent.return_value = MagicMock(key="triage", model="gpt-5.1", output_schema=None)
    provider.get_agent.return_value = None
    provider.tool_overview.return_value = {"tool_names": []}

    run_result = AgentRunResult(
        final_output="done",
        response_id="resp_1",
        usage=None,
        metadata={},
        tool_outputs=[
            {
                "type": "tool_call_item",
                "raw_item": {
                    "type": "image_generation_call",
                    "result": "dGVzdA==",
                    "id": "tc1",
                    "format": "png",
                },
            }
        ],
    )
    provider.runtime.run = AsyncMock(return_value=run_result)

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

    resp = await svc.chat(req, actor=actor)

    assert resp.attachments
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()
