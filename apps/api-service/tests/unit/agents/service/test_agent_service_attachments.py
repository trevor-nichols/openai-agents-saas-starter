import asyncio
import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationAttachment, ConversationMessage
from app.services.agents import AgentService
from app.services.agents.asset_linker import AssetLinker
from app.services.agents.context import ConversationActorContext
from app.services.agents.policy import AgentRuntimePolicy
from app.services.assets.service import AssetService
from app.services.conversation_service import ConversationService


class _StubConversationService:
    def set_repository(self, repo):  # pragma: no cover - test shim
        return None

    async def get_memory_config(self, *args, **kwargs):
        return None

    async def get_session_state(self, *args, **kwargs):
        return None

    async def append_message(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def update_session_state(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def record_conversation_created(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def append_run_events(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def persist_summary(self, *args, **kwargs):  # pragma: no cover - noop
        return None


@pytest.mark.asyncio
async def test_agent_service_stream_attaches_images(monkeypatch):
    # Mock provider runtime
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
                payload={"type": "image_generation_call", "result": "dGVzdA==", "id": "tc1", "format": "png"},
                is_terminal=False,
            )
            yield AgentStreamEvent(
                kind="run_item_stream_event",
                response_id="resp_1",
                is_terminal=True,
            )

    provider.runtime.run_stream.return_value = MockStream()

    # Storage
    storage = MagicMock()
    storage.put_object = AsyncMock()
    storage.put_object.return_value.id = uuid.uuid4()
    storage.put_object.return_value.checksum_sha256 = "abc"
    storage.put_object.return_value.created_at = None
    storage.get_presigned_download = AsyncMock(return_value=(MagicMock(url="https://u"), MagicMock()))

    svc = AgentService(
        conversation_service=cast(ConversationService, _StubConversationService()),
        provider_registry=MagicMock(get_default=lambda: provider),
        storage_service=storage,
        policy=AgentRuntimePolicy(),
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

    stream = svc.chat_stream(req, actor=actor)
    events = []
    async for ev in stream:
        events.append(ev)

    assert any(ev.attachments for ev in events)
    storage.put_object.assert_awaited()
    storage.get_presigned_download.assert_awaited()


@pytest.mark.asyncio
async def test_agent_service_asset_linking_is_best_effort():
    provider = MagicMock()
    registry = MagicMock(get_default=lambda: provider)

    class _ExplodingAssetService:
        async def link_assets_to_message(self, **_: object) -> None:
            raise RuntimeError("boom")

    linker = AssetLinker(cast(AssetService, _ExplodingAssetService()))
    attachments = [
        ConversationAttachment(
            object_id=str(uuid.uuid4()),
            filename="file.txt",
        )
    ]

    await linker.maybe_link_assets(
        tenant_id=str(uuid.uuid4()),
        message_id=1,
        attachments=attachments,
    )
