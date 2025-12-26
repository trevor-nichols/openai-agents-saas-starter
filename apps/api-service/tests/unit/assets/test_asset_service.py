import uuid
from typing import cast

import pytest

from app.domain.assets import AssetNotFoundError, AssetRecord, AssetRepository, AssetView
from app.services.assets.service import AssetService
from app.services.storage.service import StorageService


class StubAssetRepository:
    def __init__(self, asset: AssetRecord | None) -> None:
        self._asset = asset
        self._views: list[AssetView] = []

    async def get_record(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID):
        return self._asset

    async def list_by_ids(self, *, tenant_id: uuid.UUID, asset_ids):
        return self._views


class StubStorageService:
    async def get_presigned_download(self, *, tenant_id: uuid.UUID, object_id: uuid.UUID):
        raise FileNotFoundError("Object not found")

    def signed_url_ttl(self) -> int:
        return 900


@pytest.mark.asyncio
async def test_get_download_url_maps_missing_storage_to_asset_not_found() -> None:
    tenant_id = uuid.uuid4()
    asset = AssetRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        storage_object_id=uuid.uuid4(),
        asset_type="file",
        source_tool=None,
        conversation_id=None,
        message_id=None,
        tool_call_id=None,
        response_id=None,
        container_id=None,
        openai_file_id=None,
        metadata={},
    )
    service = AssetService(
        lambda: None,
        storage_service=cast(StorageService, StubStorageService()),
        repository=cast(AssetRepository, StubAssetRepository(asset)),
    )

    with pytest.raises(AssetNotFoundError, match="storage object"):
        await service.get_download_url(tenant_id=tenant_id, asset_id=asset.id)


@pytest.mark.asyncio
async def test_get_thumbnail_urls_skips_missing_and_non_images() -> None:
    tenant_id = uuid.uuid4()
    image_asset = AssetRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        storage_object_id=uuid.uuid4(),
        asset_type="image",
        source_tool=None,
        conversation_id=None,
        message_id=None,
        tool_call_id=None,
        response_id=None,
        container_id=None,
        openai_file_id=None,
        metadata={},
    )
    file_asset = AssetRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        storage_object_id=uuid.uuid4(),
        asset_type="file",
        source_tool=None,
        conversation_id=None,
        message_id=None,
        tool_call_id=None,
        response_id=None,
        container_id=None,
        openai_file_id=None,
        metadata={},
    )
    views = [
        AssetView(
            asset=image_asset,
            filename="img.png",
            mime_type="image/png",
            size_bytes=123,
            agent_key=None,
            storage_status="ready",
            storage_created_at=None,
        ),
        AssetView(
            asset=file_asset,
            filename="doc.pdf",
            mime_type="application/pdf",
            size_bytes=456,
            agent_key=None,
            storage_status="ready",
            storage_created_at=None,
        ),
    ]

    class _Repo(StubAssetRepository):
        def __init__(self):
            super().__init__(asset=None)
            self._views = views

    class _Storage:
        async def get_presigned_download(self, *, tenant_id, object_id):
            presign = type(
                "Presign",
                (),
                {"url": "https://example.com/thumb", "method": "GET", "headers": {}},
            )
            obj = type("Obj", (), {"id": object_id})
            return presign, obj

        def signed_url_ttl(self) -> int:
            return 900

    service = AssetService(
        lambda: None,
        storage_service=cast(StorageService, _Storage()),
        repository=cast(AssetRepository, _Repo()),
    )

    items, missing, unsupported = await service.get_thumbnail_urls(
        tenant_id=tenant_id,
        asset_ids=[image_asset.id, file_asset.id, uuid.uuid4()],
    )

    assert len(items) == 1
    assert items[0].asset_id == image_asset.id
    assert missing
    assert unsupported == [file_asset.id]
