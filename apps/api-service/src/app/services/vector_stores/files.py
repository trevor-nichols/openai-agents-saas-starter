"""File-level orchestration (attach/list/get/delete)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.domain.vector_stores import (
    VectorStore,
    VectorStoreFile,
    VectorStoreFileConflictError,
    VectorStoreFileRepository,
    VectorStoreNotFoundError,
    VectorStoreRepository,
)
from app.services.storage.service import StorageService
from app.services.vector_stores.gateway import OpenAIVectorStoreGateway
from app.services.vector_stores.instrumentation import instrument
from app.services.vector_stores.policy import VectorStorePolicy
from app.services.vector_stores.stores import StoreService
from app.services.vector_stores.utils import coerce_uuid

logger = logging.getLogger(__name__)


class FileService:
    def __init__(
        self,
        *,
        store_service: StoreService,
        store_repo: VectorStoreRepository,
        file_repo: VectorStoreFileRepository,
        policy: VectorStorePolicy,
        gateway: OpenAIVectorStoreGateway,
        storage_service: StorageService,
    ) -> None:
        self._store_service = store_service
        self._store_repo = store_repo
        self._file_repo = file_repo
        self._policy = policy
        self._gateway = gateway
        self._storage_service = storage_service

    async def attach_file(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        file_id: str,
        attributes: dict[str, Any] | None = None,
        chunking_strategy: dict[str, Any] | None = None,
        poll: bool = True,
    ) -> VectorStoreFile:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )

        await self._policy.ensure_file_not_attached(
            store_id=store.id, file_id=file_id, file_repo=self._file_repo
        )

        file_meta = await self._gateway.retrieve_file_meta(
            tenant_id=store.tenant_id, file_id=file_id
        )
        await self._policy.ensure_file_can_be_attached(
            tenant_id=store.tenant_id,
            store=store,
            file_meta=file_meta,
            store_repo=self._store_repo,
            file_repo=self._file_repo,
        )

        try:
            async with instrument(
                "attach_file",
                metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            ):
                remote_file = await self._gateway.attach_file(
                    tenant_id=store.tenant_id,
                    vector_store_openai_id=store.openai_id,
                    file_id=file_id,
                    attributes=attributes,
                    chunking_strategy=chunking_strategy,
                    poll=poll,
                )
        except Exception:
            logger.warning(
                "vector_store.attach.failed",
                exc_info=True,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

        usage_bytes = (
            getattr(remote_file, "usage_bytes", None) or getattr(remote_file, "bytes", 0) or 0
        )
        status = getattr(remote_file, "status", None) or "indexing"

        db_file = VectorStoreFile(
            id=uuid.uuid4(),
            openai_file_id=file_id,
            vector_store_id=store.id,
            filename=getattr(file_meta, "filename", file_id),
            mime_type=getattr(file_meta, "mime_type", None),
            size_bytes=getattr(file_meta, "bytes", None),
            usage_bytes=usage_bytes,
            status=status,
            attributes=attributes or {},
            chunking=chunking_strategy,
            last_error=getattr(remote_file, "last_error", None),
            created_at=datetime.now(UTC),
        )

        try:
            created = await self._file_repo.create(db_file)
            if usage_bytes:
                await self._store_repo.increment_usage(store_id=store.id, delta=usage_bytes)
            return created
        except IntegrityError as exc:
            await self._safe_delete_remote_file(store, file_id)
            raise VectorStoreFileConflictError(
                "File already attached to this vector store"
            ) from exc
        except Exception:
            await self._safe_delete_remote_file(store, file_id)
            raise

    async def list_files(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[VectorStoreFile], int]:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        return await self._file_repo.list(
            store_id=store.id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_file(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        openai_file_id: str,
    ) -> VectorStoreFile:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        file = await self._file_repo.get(store_id=store.id, openai_file_id=openai_file_id)
        if file is None:
            raise VectorStoreNotFoundError(
                f"File {openai_file_id} not found for vector store {vector_store_id}"
            )
        return file

    async def delete_file(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str, file_id: str
    ) -> None:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        try:
            async with instrument(
                "delete_file",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                    "file_id": file_id,
                },
            ):
                await self._gateway.delete_file(
                    tenant_id=store.tenant_id,
                    vector_store_openai_id=store.openai_id,
                    file_id=file_id,
                )
        except Exception:
            logger.warning(
                "vector_store.file_delete.failed",
                exc_info=True,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

        removed = await self._file_repo.soft_delete(store_id=store.id, openai_file_id=file_id)
        if removed:
            decrement = removed.usage_bytes or removed.size_bytes or 0
            if decrement:
                await self._store_repo.increment_usage(store_id=store.id, delta=-int(decrement))

    async def get_file_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_file_id: str
    ) -> VectorStoreFile:
        tenant_uuid = coerce_uuid(tenant_id)
        file = await self._file_repo.get_by_openai_id_for_tenant(
            tenant_id=tenant_uuid, openai_file_id=openai_file_id
        )
        if file is None:
            raise VectorStoreNotFoundError(
                f"File {openai_file_id} not found for tenant {tenant_uuid}"
            )
        return file

    async def attach_storage_object(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        object_id: uuid.UUID,
        attributes: dict[str, Any] | None = None,
        chunking_strategy: dict[str, Any] | None = None,
        poll: bool = True,
    ) -> VectorStoreFile:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )

        _, storage_obj = await self._storage_service.get_presigned_download(
            tenant_id=store.tenant_id, object_id=object_id
        )

        filename = storage_obj.filename or str(object_id)
        mime_type = storage_obj.mime_type
        data = await self._storage_service.get_object_bytes(
            tenant_id=store.tenant_id, object_id=object_id
        )
        size_bytes = len(data)

        file_meta = SimpleNamespace(bytes=size_bytes, mime_type=mime_type, filename=filename)
        await self._policy.ensure_file_can_be_attached(
            tenant_id=store.tenant_id,
            store=store,
            file_meta=file_meta,
            store_repo=self._store_repo,
            file_repo=self._file_repo,
        )

        openai_file = await self._gateway.upload_file(
            tenant_id=store.tenant_id,
            filename=filename,
            data=data,
            mime_type=mime_type,
        )
        file_id = getattr(openai_file, "id", None)
        if not file_id:
            raise RuntimeError("OpenAI file upload did not return a file id")

        await self._policy.ensure_file_not_attached(
            store_id=store.id, file_id=file_id, file_repo=self._file_repo
        )

        try:
            async with instrument(
                "attach_storage_object",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                    "object_id": str(object_id),
                },
            ):
                remote_file = await self._gateway.attach_file(
                    tenant_id=store.tenant_id,
                    vector_store_openai_id=store.openai_id,
                    file_id=file_id,
                    attributes=attributes,
                    chunking_strategy=chunking_strategy,
                    poll=poll,
                )
        except Exception:
            await self._cleanup_uploaded_file(store, file_id)
            raise

        usage_bytes = (
            getattr(remote_file, "usage_bytes", None) or getattr(remote_file, "bytes", 0) or 0
        )
        status = getattr(remote_file, "status", None) or "indexing"

        db_file = VectorStoreFile(
            id=uuid.uuid4(),
            openai_file_id=file_id,
            vector_store_id=store.id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            usage_bytes=usage_bytes,
            status=status,
            attributes=attributes or {},
            chunking=chunking_strategy,
            last_error=getattr(remote_file, "last_error", None),
            created_at=datetime.now(UTC),
        )

        try:
            created = await self._file_repo.create(db_file)
            if usage_bytes:
                await self._store_repo.increment_usage(store_id=store.id, delta=usage_bytes)
            return created
        except IntegrityError as exc:
            await self._cleanup_uploaded_file(store, file_id)
            raise VectorStoreFileConflictError(
                "File already attached to this vector store"
            ) from exc
        except Exception:
            await self._cleanup_uploaded_file(store, file_id)
            raise

    async def _safe_delete_remote_file(self, store: VectorStore, file_id: str) -> None:
        try:
            await self._gateway.delete_file(
                tenant_id=store.tenant_id,
                vector_store_openai_id=store.openai_id,
                file_id=file_id,
            )
        except Exception:  # pragma: no cover - defensive cleanup
            logger.warning(
                "vector_store.file_cleanup_failed",
                exc_info=True,
                extra={"tenant_id": str(store.tenant_id), "file_id": file_id},
            )

    async def _safe_delete_openai_file(self, *, tenant_id: uuid.UUID, file_id: str) -> None:
        try:
            await self._gateway.delete_openai_file(tenant_id=tenant_id, file_id=file_id)
        except Exception:  # pragma: no cover - defensive cleanup
            logger.warning(
                "vector_store.file_openai_cleanup_failed",
                exc_info=True,
                extra={"tenant_id": str(tenant_id), "file_id": file_id},
            )

    async def _cleanup_uploaded_file(self, store: VectorStore, file_id: str) -> None:
        await self._safe_delete_remote_file(store, file_id)
        await self._safe_delete_openai_file(tenant_id=store.tenant_id, file_id=file_id)


__all__ = ["FileService"]
