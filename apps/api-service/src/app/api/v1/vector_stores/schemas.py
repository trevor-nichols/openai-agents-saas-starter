from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class VectorStoreCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    expires_after: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class VectorStoreResponse(BaseModel):
    id: UUID
    openai_id: str
    tenant_id: UUID
    owner_user_id: UUID | None
    name: str
    description: str | None
    status: str
    usage_bytes: int
    expires_after: dict[str, Any] | None = None
    expires_at: datetime | None = None
    last_active_at: datetime | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class VectorStoreListResponse(BaseModel):
    items: list[VectorStoreResponse]
    total: int


class VectorStoreFileCreateRequest(BaseModel):
    file_id: str = Field(min_length=1)
    attributes: dict[str, Any] | None = None
    chunking_strategy: dict[str, Any] | None = None
    poll: bool = True


class VectorStoreFileResponse(BaseModel):
    id: UUID
    openai_file_id: str
    vector_store_id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int | None
    usage_bytes: int
    status: str
    attributes: dict[str, Any]
    chunking_strategy: dict[str, Any] | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class VectorStoreFileListResponse(BaseModel):
    items: list[VectorStoreFileResponse]
    total: int


class VectorStoreSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    filters: dict[str, Any] | None = None
    max_num_results: int | None = Field(default=None, ge=1, le=50)
    ranking_options: dict[str, Any] | None = None


class VectorStoreSearchResponse(BaseModel):
    data: Any


__all__ = [
    "VectorStoreCreateRequest",
    "VectorStoreResponse",
    "VectorStoreListResponse",
    "VectorStoreFileCreateRequest",
    "VectorStoreFileResponse",
    "VectorStoreFileListResponse",
    "VectorStoreSearchRequest",
    "VectorStoreSearchResponse",
]
