"""Service layer for asset catalog operations."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime

from app.domain.assets import (
    AssetNotFoundError,
    AssetRecord,
    AssetRepository,
    AssetSourceTool,
    AssetType,
    AssetView,
)
from app.infrastructure.persistence.assets.repository import SqlAlchemyAssetRepository
from app.services.storage.service import StorageService


class AssetService:
    """Coordinates asset metadata with storage operations."""

    def __init__(
        self,
        session_factory,
        storage_service: StorageService,
        repository: AssetRepository | None = None,
    ) -> None:
        self._repository = repository or SqlAlchemyAssetRepository(session_factory)
        self._storage_service = storage_service

    async def create_asset(
        self,
        *,
        tenant_id: uuid.UUID,
        storage_object_id: uuid.UUID,
        asset_type: AssetType,
        source_tool: AssetSourceTool | None,
        conversation_id: uuid.UUID | None,
        message_id: int | None,
        tool_call_id: str | None,
        response_id: str | None,
        container_id: str | None,
        openai_file_id: str | None,
        metadata: dict[str, object] | None = None,
    ) -> AssetRecord:
        asset = AssetRecord(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            storage_object_id=storage_object_id,
            asset_type=asset_type,
            source_tool=source_tool,
            conversation_id=conversation_id,
            message_id=message_id,
            tool_call_id=tool_call_id,
            response_id=response_id,
            container_id=container_id,
            openai_file_id=openai_file_id,
            metadata=metadata or {},
        )
        return await self._repository.create(asset)

    async def list_assets(
        self,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        asset_type: AssetType | None = None,
        source_tool: AssetSourceTool | None = None,
        conversation_id: uuid.UUID | None = None,
        message_id: int | None = None,
        agent_key: str | None = None,
        mime_type_prefix: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[AssetView]:
        return await self._repository.list(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            asset_type=asset_type,
            source_tool=source_tool,
            conversation_id=conversation_id,
            message_id=message_id,
            agent_key=agent_key,
            mime_type_prefix=mime_type_prefix,
            created_after=created_after,
            created_before=created_before,
        )

    async def get_asset(
        self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID
    ) -> AssetView:
        asset = await self._repository.get(tenant_id=tenant_id, asset_id=asset_id)
        if asset is None:
            raise AssetNotFoundError("Asset not found")
        return asset

    async def get_download_url(
        self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID
    ):
        asset = await self._repository.get_record(tenant_id=tenant_id, asset_id=asset_id)
        if asset is None:
            raise AssetNotFoundError("Asset not found")
        try:
            return await self._storage_service.get_presigned_download(
                tenant_id=tenant_id,
                object_id=asset.storage_object_id,
            )
        except FileNotFoundError as exc:
            raise AssetNotFoundError("Asset storage object not found") from exc

    def signed_url_ttl(self) -> int:
        return self._storage_service.signed_url_ttl()

    async def delete_asset(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> None:
        asset = await self._repository.get_record(tenant_id=tenant_id, asset_id=asset_id)
        if asset is None:
            raise AssetNotFoundError("Asset not found")
        await self._storage_service.delete_object(
            tenant_id=tenant_id,
            object_id=asset.storage_object_id,
        )
        await self._repository.mark_deleted(tenant_id=tenant_id, asset_id=asset_id)

    async def link_assets_to_message(
        self,
        *,
        tenant_id: uuid.UUID,
        message_id: int,
        storage_object_ids: Iterable[uuid.UUID],
    ) -> int:
        ids = [uuid.UUID(str(oid)) for oid in storage_object_ids]
        return await self._repository.link_message(
            tenant_id=tenant_id, message_id=message_id, storage_object_ids=ids
        )


__all__ = ["AssetService"]
