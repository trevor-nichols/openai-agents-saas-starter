"""Domain models and contracts for generated assets."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

AssetType = Literal["image", "file"]
AssetSourceTool = Literal["image_generation", "code_interpreter", "user_upload", "unknown"]


class AssetNotFoundError(RuntimeError):
    """Raised when an asset lookup fails for a tenant."""


@dataclass(slots=True)
class AssetRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    storage_object_id: uuid.UUID
    asset_type: AssetType
    source_tool: AssetSourceTool | None
    conversation_id: uuid.UUID | None
    message_id: int | None
    tool_call_id: str | None
    response_id: str | None
    container_id: str | None
    openai_file_id: str | None
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass(slots=True)
class AssetView:
    asset: AssetRecord
    filename: str | None
    mime_type: str | None
    size_bytes: int | None
    agent_key: str | None
    storage_status: str | None
    storage_created_at: datetime | None


@dataclass(slots=True)
class AssetThumbnailUrl:
    asset_id: uuid.UUID
    storage_object_id: uuid.UUID
    download_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class AssetRepository(Protocol):
    async def create(self, asset: AssetRecord) -> AssetRecord: ...

    async def get(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> AssetView | None: ...

    async def get_record(
        self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID
    ) -> AssetRecord | None: ...

    async def list(
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
    ) -> list[AssetView]: ...

    async def list_by_ids(
        self, *, tenant_id: uuid.UUID, asset_ids: Sequence[uuid.UUID]
    ) -> Sequence[AssetView]: ...

    async def mark_deleted(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> None: ...

    async def link_message(
        self,
        *,
        tenant_id: uuid.UUID,
        message_id: int,
        storage_object_ids: Sequence[uuid.UUID],
    ) -> int: ...

    async def get_by_storage_object(
        self, *, tenant_id: uuid.UUID, storage_object_id: uuid.UUID
    ) -> AssetRecord | None: ...


__all__ = [
    "AssetType",
    "AssetSourceTool",
    "AssetRecord",
    "AssetView",
    "AssetThumbnailUrl",
    "AssetRepository",
    "AssetNotFoundError",
]
