from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.domain.input_attachments import InputAttachmentNotFoundError, InputAttachmentRef
from app.services.agents.input_attachments import InputAttachmentService


class _FakeStorageService:
    def __init__(self) -> None:
        self.objects: dict[uuid.UUID, SimpleNamespace] = {}
        self.calls: list[uuid.UUID] = []

    def add_object(self, *, object_id: uuid.UUID, mime_type: str, filename: str) -> None:
        self.objects[object_id] = SimpleNamespace(
            id=object_id,
            mime_type=mime_type,
            filename=filename,
            size_bytes=123,
            status="ready",
        )

    async def get_presigned_download(self, *, tenant_id, object_id):
        self.calls.append(object_id)
        obj = self.objects.get(object_id)
        if obj is None:
            raise FileNotFoundError("Object not found")
        presigned = SimpleNamespace(url=f"https://example.com/{object_id}")
        return presigned, obj


class _FakeAssetService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def create_asset(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=uuid.uuid4())


class _FailingAssetService:
    async def create_asset(self, **kwargs):
        raise RuntimeError("asset create failed")


@pytest.mark.asyncio
async def test_input_attachments_resolves_image_and_records_asset():
    storage = _FakeStorageService()
    asset_service = _FakeAssetService()
    obj_id = uuid.uuid4()
    storage.add_object(object_id=obj_id, mime_type="image/png", filename="image.png")

    service = InputAttachmentService(
        lambda: storage,
        asset_service_resolver=lambda: asset_service,
    )
    actor = SimpleNamespace(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="22222222-2222-2222-2222-222222222222",
    )

    resolution = await service.resolve(
        [InputAttachmentRef(object_id=obj_id)],
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="triage",
    )

    assert resolution.input_items
    assert resolution.input_items[0]["type"] == "input_image"
    assert resolution.attachments[0].filename == "image.png"
    assert asset_service.calls
    assert asset_service.calls[0]["asset_type"] == "image"


@pytest.mark.asyncio
async def test_input_attachments_rejects_non_image_kind():
    storage = _FakeStorageService()
    obj_id = uuid.uuid4()
    storage.add_object(object_id=obj_id, mime_type="application/pdf", filename="doc.pdf")

    service = InputAttachmentService(lambda: storage)
    actor = SimpleNamespace(tenant_id="11111111-1111-1111-1111-111111111111", user_id="u")

    with pytest.raises(ValueError, match="requires an image"):
        await service.resolve(
            [InputAttachmentRef(object_id=obj_id, kind="image")],
            actor=actor,
            conversation_id="33333333-3333-3333-3333-333333333333",
            agent_key="triage",
        )


@pytest.mark.asyncio
async def test_input_attachments_missing_object_raises_not_found():
    storage = _FakeStorageService()
    obj_id = uuid.uuid4()

    service = InputAttachmentService(lambda: storage)
    actor = SimpleNamespace(tenant_id="11111111-1111-1111-1111-111111111111", user_id="u")

    with pytest.raises(InputAttachmentNotFoundError, match="Attachment not found"):
        await service.resolve(
            [InputAttachmentRef(object_id=obj_id)],
            actor=actor,
            conversation_id="33333333-3333-3333-3333-333333333333",
            agent_key="triage",
        )


@pytest.mark.asyncio
async def test_input_attachments_asset_failure_is_best_effort():
    storage = _FakeStorageService()
    obj_id = uuid.uuid4()
    storage.add_object(object_id=obj_id, mime_type="image/png", filename="image.png")

    service = InputAttachmentService(
        lambda: storage,
        asset_service_resolver=lambda: _FailingAssetService(),
    )
    actor = SimpleNamespace(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="22222222-2222-2222-2222-222222222222",
    )

    resolution = await service.resolve(
        [InputAttachmentRef(object_id=obj_id)],
        actor=actor,
        conversation_id="33333333-3333-3333-3333-333333333333",
        agent_key="triage",
    )

    assert resolution.attachments
