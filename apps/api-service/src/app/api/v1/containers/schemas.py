from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ContainerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    memory_limit: str | None = Field(default=None, description="1g, 4g, 16g, or 64g")
    expires_after: dict[str, Any] | None = None
    file_ids: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ContainerResponse(BaseModel):
    id: UUID
    openai_id: str
    tenant_id: UUID
    owner_user_id: UUID | None
    name: str
    memory_limit: str
    status: str
    expires_after: dict[str, Any] | None
    last_active_at: datetime | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ContainerListResponse(BaseModel):
    items: list[ContainerResponse]
    total: int


class ContainerBindRequest(BaseModel):
    container_id: UUID


__all__ = [
    "ContainerCreateRequest",
    "ContainerResponse",
    "ContainerListResponse",
    "ContainerBindRequest",
]
