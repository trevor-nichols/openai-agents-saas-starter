"""Pydantic schemas for storage endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StoragePresignUploadRequest(BaseModel):
    filename: str = Field(..., max_length=256)
    mime_type: str = Field(..., max_length=128)
    size_bytes: int = Field(..., ge=0)
    agent_key: str | None = Field(default=None, max_length=64)
    conversation_id: uuid.UUID | None = None
    metadata: dict[str, Any] | None = None


class StoragePresignUploadResponse(BaseModel):
    object_id: uuid.UUID
    upload_url: str
    method: str
    headers: dict[str, str]
    bucket: str
    object_key: str
    expires_in_seconds: int


class StoragePresignDownloadResponse(BaseModel):
    object_id: uuid.UUID
    download_url: str
    method: str
    headers: dict[str, str]
    bucket: str
    object_key: str
    expires_in_seconds: int


class StorageObjectResponse(BaseModel):
    id: uuid.UUID
    bucket: str
    object_key: str
    filename: str | None
    mime_type: str | None
    size_bytes: int | None
    status: str | None
    created_at: datetime | None
    conversation_id: uuid.UUID | None
    agent_key: str | None


class StorageObjectListResponse(BaseModel):
    items: list[StorageObjectResponse]
    next_offset: int | None = None
