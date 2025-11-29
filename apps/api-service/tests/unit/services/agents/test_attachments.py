import uuid
from collections import defaultdict
from typing import cast

import pytest

from app.domain.conversations import ConversationAttachment, ConversationMessage
from app.services.agents.attachments import AttachmentService
from app.services.storage.service import StorageService


class FakeStorageService:
    def __init__(self):
        self.put_calls = []
        self.presigned_for = defaultdict(list)

    async def put_object(self, *, tenant_id, user_id, data, filename, mime_type, agent_key, conversation_id, metadata):
        oid = uuid.uuid4()
        self.put_calls.append((tenant_id, filename, mime_type, metadata))
        return type("Obj", (), {"id": oid})

    async def get_presigned_download(self, *, tenant_id, object_id):
        self.presigned_for[tenant_id].append(object_id)
        return type("Presigned", (), {"url": f"https://example.com/{object_id}"}), None


def attachment_service(storage: FakeStorageService) -> AttachmentService:
    return AttachmentService(lambda: cast(StorageService, storage))


@pytest.mark.asyncio
async def test_ingest_image_outputs_happy_path(monkeypatch):
    storage = FakeStorageService()
    service = attachment_service(storage)
    actor = type("Actor", (), {"tenant_id": "11111111-1111-1111-1111-111111111111", "user_id": "22222222-2222-2222-2222-222222222222"})
    outputs = [
        {
            "type": "image_generation_call",
            "id": "tool-1",
            "result": "ZmFrZQ==",  # base64("fake")
            "format": "png",
        }
    ]

    attachments = await service.ingest_image_outputs(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="code",
        response_id="resp-1",
    )

    assert len(attachments) == 1
    att = attachments[0]
    assert att.tool_call_id == "tool-1"
    assert att.presigned_url.startswith("https://example.com/")


@pytest.mark.asyncio
async def test_ingest_image_outputs_skips_non_image():
    storage = FakeStorageService()
    service = attachment_service(storage)
    actor = type("Actor", (), {"tenant_id": "11111111-1111-1111-1111-111111111111", "user_id": "22222222-2222-2222-2222-222222222222"})

    outputs = [{"type": "not_image"}]
    attachments = await service.ingest_image_outputs(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="code",
        response_id="resp-1",
    )

    assert attachments == []


@pytest.mark.asyncio
async def test_ingest_image_outputs_deduplicates_tool_call(monkeypatch):
    storage = FakeStorageService()
    service = attachment_service(storage)
    actor = type("Actor", (), {"tenant_id": "11111111-1111-1111-1111-111111111111", "user_id": "22222222-2222-2222-2222-222222222222"})
    outputs = [
        {"type": "image_generation_call", "id": "tool-1", "result": "ZmFrZQ==", "format": "png"},
        {"type": "image_generation_call", "id": "tool-1", "result": "ZmFrZQ==", "format": "png"},
    ]

    seen = set()
    attachments = await service.ingest_image_outputs(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="code",
        response_id="resp-1",
        seen_tool_calls=seen,
    )

    assert len(attachments) == 1
    assert seen == {"tool-1"}


@pytest.mark.asyncio
async def test_presign_message_attachments_skips_when_none():
    storage = FakeStorageService()
    service = attachment_service(storage)

    messages = [ConversationMessage(role="user", content="hi", attachments=[])]
    await service.presign_message_attachments(messages, tenant_id="11111111-1111-1111-1111-111111111111")
    assert storage.presigned_for == {}


@pytest.mark.asyncio
async def test_presign_message_attachments_adds_urls():
    storage = FakeStorageService()
    service = attachment_service(storage)
    att = ConversationAttachment(
        object_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        filename="f.png",
        mime_type="image/png",
        size_bytes=4,
        tool_call_id=None,
        presigned_url=None,
    )
    messages = [ConversationMessage(role="assistant", content="done", attachments=[att])]

    await service.presign_message_attachments(messages, tenant_id="11111111-1111-1111-1111-111111111111")

    assert att.presigned_url.startswith("https://example.com/")
    assert storage.presigned_for
