import uuid

import pytest

from app.domain.assets import AssetNotFoundError, AssetRecord
from app.services.assets.service import AssetService


class StubAssetRepository:
    def __init__(self, asset: AssetRecord | None) -> None:
        self._asset = asset

    async def get_record(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID):
        return self._asset


class StubStorageService:
    async def get_presigned_download(self, *, tenant_id: uuid.UUID, object_id: uuid.UUID):
        raise FileNotFoundError("Object not found")


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
        storage_service=StubStorageService(),
        repository=StubAssetRepository(asset),
    )

    with pytest.raises(AssetNotFoundError, match="storage object"):
        await service.get_download_url(tenant_id=tenant_id, asset_id=asset.id)
