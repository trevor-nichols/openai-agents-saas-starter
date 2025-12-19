"""Domain models and contracts for tenant-scoped vector stores."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

# --- Exceptions ---

class VectorStoreNotFoundError(RuntimeError):
    """Raised when a vector store or file cannot be found for a tenant."""


class VectorStoreQuotaError(RuntimeError):
    """Raised when tenant or store limits are exceeded."""


class VectorStoreNameConflictError(RuntimeError):
    """Raised when a store name collides within a tenant."""


class VectorStoreValidationError(RuntimeError):
    """Raised when inputs fail validation (size, mime, etc.)."""


class VectorStoreFileConflictError(RuntimeError):
    """Raised when the same file is attached twice to a store."""


# --- Domain models ---


@dataclass(slots=True)
class VectorStore:
    id: uuid.UUID
    openai_id: str
    tenant_id: uuid.UUID
    owner_user_id: uuid.UUID | None
    name: str
    description: str | None
    status: str
    usage_bytes: int
    expires_after: dict[str, object] | None
    expires_at: datetime | None
    last_active_at: datetime | None
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass(slots=True)
class VectorStoreFile:
    id: uuid.UUID
    openai_file_id: str
    vector_store_id: uuid.UUID
    filename: str
    mime_type: str | None
    size_bytes: int | None
    usage_bytes: int
    status: str
    attributes: dict[str, object] = field(default_factory=dict)
    chunking: dict[str, object] | None = None
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass(slots=True)
class AgentVectorStoreBinding:
    agent_key: str
    vector_store_id: uuid.UUID
    tenant_id: uuid.UUID


# --- Search models ---


@dataclass(slots=True)
class VectorStoreSearchContentChunk:
    type: str
    text: str


@dataclass(slots=True)
class VectorStoreSearchResult:
    file_id: str
    filename: str
    score: float
    attributes: dict[str, object] = field(default_factory=dict)
    content: list[VectorStoreSearchContentChunk] = field(default_factory=list)


@dataclass(slots=True)
class VectorStoreSearchResultsPage:
    object: str
    search_query: str
    data: list[VectorStoreSearchResult] = field(default_factory=list)
    has_more: bool = False
    next_page: str | None = None


# --- Repository contracts ---


class VectorStoreRepository(Protocol):
    async def create(self, store: VectorStore) -> VectorStore: ...

    async def list(
        self, *, tenant_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[VectorStore], int]: ...

    async def get(self, store_id: uuid.UUID) -> VectorStore | None: ...

    async def get_by_name(self, *, tenant_id: uuid.UUID, name: str) -> VectorStore | None: ...

    async def get_by_openai_id(
        self, *, tenant_id: uuid.UUID, openai_id: str
    ) -> VectorStore | None: ...

    async def soft_delete(self, store_id: uuid.UUID) -> None: ...

    async def count_active(self, *, tenant_id: uuid.UUID) -> int: ...

    async def increment_usage(self, *, store_id: uuid.UUID, delta: int) -> None: ...

    async def sum_usage(self, *, tenant_id: uuid.UUID) -> int: ...


class VectorStoreFileRepository(Protocol):
    async def create(self, file: VectorStoreFile) -> VectorStoreFile: ...

    async def list(
        self, *, store_id: uuid.UUID, status: str | None, limit: int, offset: int
    ) -> tuple[list[VectorStoreFile], int]: ...

    async def get(
        self, *, store_id: uuid.UUID, openai_file_id: str
    ) -> VectorStoreFile | None: ...

    async def soft_delete(
        self, *, store_id: uuid.UUID, openai_file_id: str
    ) -> VectorStoreFile | None: ...

    async def count_active(self, *, store_id: uuid.UUID) -> int: ...

    async def get_by_openai_id_for_tenant(
        self, *, tenant_id: uuid.UUID, openai_file_id: str
    ) -> VectorStoreFile | None: ...


class AgentVectorStoreRepository(Protocol):
    async def get_binding(
        self, *, tenant_id: uuid.UUID, agent_key: str
    ) -> AgentVectorStoreBinding | None: ...

    async def upsert_binding(self, binding: AgentVectorStoreBinding) -> AgentVectorStoreBinding: ...

    async def delete_binding(
        self, *, tenant_id: uuid.UUID, agent_key: str, vector_store_id: uuid.UUID
    ) -> None: ...


__all__ = [
    "VectorStore",
    "VectorStoreFile",
    "AgentVectorStoreBinding",
    "VectorStoreSearchContentChunk",
    "VectorStoreSearchResult",
    "VectorStoreSearchResultsPage",
    "VectorStoreRepository",
    "VectorStoreFileRepository",
    "AgentVectorStoreRepository",
    "VectorStoreNotFoundError",
    "VectorStoreQuotaError",
    "VectorStoreNameConflictError",
    "VectorStoreValidationError",
    "VectorStoreFileConflictError",
]
