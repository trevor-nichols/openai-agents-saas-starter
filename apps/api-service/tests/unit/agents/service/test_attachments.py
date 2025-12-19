import uuid
from collections import defaultdict
from typing import cast

import pytest

from app.domain.conversations import ConversationAttachment, ConversationMessage
from app.services.agents.attachments import AttachmentService
from app.services.containers.files_gateway import ContainerFileContent, ContainerFilesGateway
from app.services.assets.service import AssetService
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


class FakeAssetService:
    def __init__(self):
        self.calls = []

    async def create_asset(self, **kwargs):
        self.calls.append(kwargs)
        return type("Asset", (), {"id": uuid.uuid4()})


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


class FakeContainerFilesGateway:
    def __init__(self, *, data: bytes, filename: str | None = None):
        self.calls: list[tuple[uuid.UUID, str, str]] = []
        self._data = data
        self._filename = filename

    async def download_file_content(self, *, tenant_id, container_id, file_id):
        self.calls.append((uuid.UUID(str(tenant_id)), str(container_id), str(file_id)))
        return ContainerFileContent(data=self._data, filename=self._filename)


@pytest.mark.asyncio
async def test_ingest_container_file_citations_happy_path():
    storage = FakeStorageService()
    gateway = FakeContainerFilesGateway(data=b"a,b\n1,2\n", filename="squares.csv")
    service = AttachmentService(
        lambda: cast(StorageService, storage),
        container_files_gateway_resolver=lambda: cast(ContainerFilesGateway, gateway),
    )
    actor = type(
        "Actor",
        (),
        {
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "22222222-2222-2222-2222-222222222222",
        },
    )
    outputs = [
        {
            "type": "message",
            "content": [
                {
                    "type": "output_text",
                    "text": "download squares.csv",
                    "annotations": [
                        {
                            "type": "container_file_citation",
                            "container_id": "cntr_123",
                            "file_id": "cfile_123",
                            "filename": "squares.csv",
                        }
                    ],
                }
            ],
        }
    ]

    attachments = await service.ingest_container_file_citations(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="researcher",
        response_id="resp-1",
    )

    assert len(attachments) == 1
    att = attachments[0]
    assert att.filename == "squares.csv"
    assert att.mime_type == "text/csv"
    assert att.size_bytes == len(b"a,b\n1,2\n")
    assert att.presigned_url and att.presigned_url.startswith("https://example.com/")
    assert gateway.calls == [
        (uuid.UUID(actor.tenant_id), "cntr_123", "cfile_123"),
    ]
    assert storage.put_calls, "Expected storage.put_object call"
    _, stored_name, stored_mime, stored_meta = storage.put_calls[0]
    assert stored_name == "squares.csv"
    assert stored_mime == "text/csv"
    assert stored_meta["container_id"] == "cntr_123"
    assert stored_meta["file_id"] == "cfile_123"


@pytest.mark.asyncio
async def test_ingest_container_file_citations_deduplicates_repeated_citations():
    storage = FakeStorageService()
    gateway = FakeContainerFilesGateway(data=b"abc", filename="report.pdf")
    service = AttachmentService(
        lambda: cast(StorageService, storage),
        container_files_gateway_resolver=lambda: cast(ContainerFilesGateway, gateway),
    )
    actor = type(
        "Actor",
        (),
        {
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "22222222-2222-2222-2222-222222222222",
        },
    )
    outputs = [
        {
            "type": "container_file_citation",
            "container_id": "cntr_123",
            "file_id": "cfile_123",
            "filename": "report.pdf",
        },
        {
            "type": "container_file_citation",
            "container_id": "cntr_123",
            "file_id": "cfile_123",
            "filename": "report.pdf",
        },
    ]

    attachments = await service.ingest_container_file_citations(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="researcher",
        response_id="resp-1",
    )

    assert len(attachments) == 1
    assert len(storage.put_calls) == 1
    assert len(gateway.calls) == 1


@pytest.mark.asyncio
async def test_ingest_image_outputs_records_asset():
    storage = FakeStorageService()
    asset_service = FakeAssetService()
    service = AttachmentService(
        lambda: cast(StorageService, storage),
        asset_service_resolver=lambda: cast(AssetService, asset_service),
    )
    actor = type(
        "Actor",
        (),
        {
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "22222222-2222-2222-2222-222222222222",
        },
    )
    outputs = [
        {
            "type": "image_generation_call",
            "id": "tool-2",
            "result": "ZmFrZQ==",  # base64("fake")
            "format": "png",
        }
    ]

    attachments = await service.ingest_image_outputs(
        outputs,
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="image",
        response_id="resp-2",
    )

    assert len(attachments) == 1
    assert len(asset_service.calls) == 1
    assert asset_service.calls[0]["asset_type"] == "image"


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
