from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.vector_stores import (
    VectorStoreSearchContentChunk,
    VectorStoreSearchResult,
    VectorStoreSearchResultsPage,
)


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


class VectorStoreFileUploadRequest(BaseModel):
    object_id: UUID
    agent_key: str = Field(min_length=1)
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
    query: str | list[str] = Field(min_length=1)
    filters: dict[str, Any] | None = None
    max_num_results: int | None = Field(default=None, ge=1, le=50)
    ranking_options: dict[str, Any] | None = None


class VectorStoreSearchContentChunkResponse(BaseModel):
    type: Literal["text"]
    text: str

    @classmethod
    def from_domain(
        cls, chunk: VectorStoreSearchContentChunk
    ) -> VectorStoreSearchContentChunkResponse:
        return cls(type="text", text=chunk.text)


class VectorStoreSearchResultResponse(BaseModel):
    file_id: str
    filename: str
    score: float
    attributes: dict[str, Any] = Field(default_factory=dict)
    content: list[VectorStoreSearchContentChunkResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: VectorStoreSearchResult) -> VectorStoreSearchResultResponse:
        return cls(
            file_id=result.file_id,
            filename=result.filename,
            score=result.score,
            attributes=dict(result.attributes),
            content=[VectorStoreSearchContentChunkResponse.from_domain(c) for c in result.content],
        )


class VectorStoreSearchResponse(BaseModel):
    object: str
    search_query: str
    data: list[VectorStoreSearchResultResponse] = Field(default_factory=list)
    has_more: bool = False
    next_page: str | None = None

    @classmethod
    def from_domain(cls, page: VectorStoreSearchResultsPage) -> VectorStoreSearchResponse:
        return cls(
            object=page.object,
            search_query=page.search_query,
            data=[VectorStoreSearchResultResponse.from_domain(item) for item in page.data],
            has_more=page.has_more,
            next_page=page.next_page,
        )


__all__ = [
    "VectorStoreCreateRequest",
    "VectorStoreResponse",
    "VectorStoreListResponse",
    "VectorStoreFileCreateRequest",
    "VectorStoreFileUploadRequest",
    "VectorStoreFileResponse",
    "VectorStoreFileListResponse",
    "VectorStoreSearchRequest",
    "VectorStoreSearchResponse",
    "VectorStoreSearchContentChunkResponse",
    "VectorStoreSearchResultResponse",
]
