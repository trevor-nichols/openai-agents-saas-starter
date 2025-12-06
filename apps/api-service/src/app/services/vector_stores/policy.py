"""Guardrails and validation for vector store operations."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from app.core.settings import Settings
from app.domain.vector_stores import (
    VectorStore,
    VectorStoreFileConflictError,
    VectorStoreFileRepository,
    VectorStoreNameConflictError,
    VectorStoreQuotaError,
    VectorStoreRepository,
    VectorStoreValidationError,
)
from app.services.vector_stores.limits import VectorLimitResolver, VectorLimits


class VectorStorePolicy:
    def __init__(
        self,
        limits_resolver: VectorLimitResolver,
        settings_factory: Callable[[], Settings],
    ) -> None:
        self._limits_resolver = limits_resolver
        self._settings_factory = settings_factory

    async def resolve_limits(self, tenant_id: uuid.UUID) -> VectorLimits:
        return await self._limits_resolver.resolve(str(tenant_id))

    async def ensure_store_can_be_created(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        store_repo: VectorStoreRepository,
    ) -> VectorLimits:
        limits = await self.resolve_limits(tenant_id)
        if limits.max_stores_per_tenant is not None:
            current = await store_repo.count_active(tenant_id=tenant_id)
            if current >= limits.max_stores_per_tenant:
                raise VectorStoreQuotaError("Maximum vector stores reached for tenant")

        existing = await store_repo.get_by_name(tenant_id=tenant_id, name=name)
        if existing:
            raise VectorStoreNameConflictError("A vector store with this name already exists")
        return limits

    async def ensure_file_can_be_attached(
        self,
        *,
        tenant_id: uuid.UUID,
        store: VectorStore,
        file_meta: object,
        store_repo: VectorStoreRepository,
        file_repo: VectorStoreFileRepository,
    ) -> VectorLimits:
        limits = await self.resolve_limits(tenant_id)
        settings = self._settings_factory()

        size_bytes = getattr(file_meta, "bytes", None)
        if size_bytes is not None and size_bytes > limits.max_file_bytes:
            raise VectorStoreValidationError(
                f"File exceeds maximum size of {int(limits.max_file_bytes / 1024 / 1024)} MB"
            )

        mime = getattr(file_meta, "mime_type", None)
        if (
            mime
            and settings.vector_allowed_mime_types
            and mime not in settings.vector_allowed_mime_types
        ):
            raise VectorStoreValidationError("MIME type not allowed for vector store indexing")

        if limits.max_files_per_store is not None:
            count = await file_repo.count_active(store_id=store.id)
            if count >= limits.max_files_per_store:
                raise VectorStoreQuotaError("Maximum files reached for this vector store")

        if limits.max_total_bytes is not None and size_bytes is not None:
            total_bytes = await store_repo.sum_usage(tenant_id=tenant_id)
            projected = total_bytes + int(size_bytes)
            if projected > limits.max_total_bytes:
                raise VectorStoreQuotaError("Tenant vector store byte cap exceeded")

        return limits

    async def ensure_file_not_attached(
        self,
        *,
        store_id: uuid.UUID,
        file_id: str,
        file_repo: VectorStoreFileRepository,
    ) -> None:
        existing = await file_repo.get(store_id=store_id, openai_file_id=file_id)
        if existing:
            raise VectorStoreFileConflictError("File already attached to this vector store")


__all__ = ["VectorStorePolicy"]
