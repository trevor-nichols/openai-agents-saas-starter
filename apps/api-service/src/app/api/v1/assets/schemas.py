"""Pydantic schemas for asset catalog endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AssetType = Literal["image", "file"]
AssetSourceTool = Literal["image_generation", "code_interpreter", "user_upload", "unknown"]


class AssetResponse(BaseModel):
    id: uuid.UUID
    storage_object_id: uuid.UUID
    asset_type: AssetType
    source_tool: AssetSourceTool | None = None
    conversation_id: uuid.UUID | None = None
    message_id: int | None = None
    tool_call_id: str | None = None
    response_id: str | None = None
    container_id: str | None = None
    openai_file_id: str | None = None
    metadata: dict[str, Any] | None = None

    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    agent_key: str | None = None
    storage_status: str | None = None

    asset_created_at: datetime | None = None
    asset_updated_at: datetime | None = None
    storage_created_at: datetime | None = None


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    next_offset: int | None = None


class AssetDownloadResponse(BaseModel):
    asset_id: uuid.UUID
    storage_object_id: uuid.UUID
    download_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class AssetThumbnailUrlItem(BaseModel):
    asset_id: uuid.UUID
    storage_object_id: uuid.UUID
    download_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class AssetThumbnailUrlsRequest(BaseModel):
    asset_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)


class AssetThumbnailUrlsResponse(BaseModel):
    items: list[AssetThumbnailUrlItem]
    missing_asset_ids: list[uuid.UUID] = Field(default_factory=list)
    unsupported_asset_ids: list[uuid.UUID] = Field(default_factory=list)


class AssetListFilters(BaseModel):
    asset_type: AssetType | None = Field(default=None)
    source_tool: AssetSourceTool | None = Field(default=None)
    conversation_id: uuid.UUID | None = Field(default=None)
    message_id: int | None = Field(default=None, ge=1)
    agent_key: str | None = Field(default=None, max_length=64)
    mime_type_prefix: str | None = Field(default=None, max_length=64)
    created_after: datetime | None = Field(default=None)
    created_before: datetime | None = Field(default=None)
