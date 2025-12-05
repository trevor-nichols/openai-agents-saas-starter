"""Service layer for OpenAI vector stores and file search orchestration."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from agents import trace
from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.vector_stores.models import (
    AgentVectorStore,
    VectorStore,
    VectorStoreFile,
)
from app.observability.metrics import (
    VECTOR_STORE_OPERATION_DURATION_SECONDS,
    VECTOR_STORE_OPERATIONS_TOTAL,
)
from app.services.vector_stores.limits import VectorLimitResolver, VectorLimits

logger = logging.getLogger(__name__)


class VectorStoreNotFoundError(RuntimeError):
    pass


class VectorStoreQuotaError(RuntimeError):
    pass


class VectorStoreNameConflictError(RuntimeError):
    pass


class VectorStoreValidationError(RuntimeError):
    pass


class VectorStoreFileConflictError(RuntimeError):
    pass


def _coerce_uuid(value: uuid.UUID | str | None) -> uuid.UUID:
    if value is None:
        raise ValueError("UUID value is required")
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception as exc:
        raise ValueError(f"Invalid UUID value: {value}") from exc


def _coerce_uuid_optional(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None:
        return None
    return _coerce_uuid(value)


class VectorStoreService:
    """Coordinates OpenAI vector store API calls with local persistence."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings_factory: Callable[[], Settings],
        *,
        get_tenant_api_key: Callable[[uuid.UUID, Settings], str] | None = None,
        limit_resolver: VectorLimitResolver | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings_factory = settings_factory
        self._get_tenant_api_key = get_tenant_api_key
        self._limit_resolver = limit_resolver

    # -------- Public API --------
    async def create_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        owner_user_id: uuid.UUID | str | None,
        name: str,
        description: str | None = None,
        expires_after: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VectorStore:
        tenant_uuid = _coerce_uuid(tenant_id)
        owner_uuid = _coerce_uuid_optional(owner_user_id)

        limits = await self._resolve_limits(tenant_uuid)
        await self._enforce_store_limit(tenant_uuid, limits)
        await self._ensure_unique_name(tenant_uuid, name)
        client = self._openai_client(tenant_uuid)
        t0 = perf_counter()
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if expires_after is not None:
            payload["expires_after"] = expires_after
        if metadata is not None:
            payload["metadata"] = metadata
        try:
            with trace(
                workflow_name="vector_store.create",
                metadata={"tenant_id": str(tenant_uuid)},
            ):
                remote = await client.vector_stores.create(**payload)
            self._observe("create_store", "success", t0)
        except Exception as exc:
            self._observe("create_store", "error", t0)
            logger.warning(
                "vector_store.create.failed",
                exc_info=exc,
                extra={"tenant_id": str(tenant_id)},
            )
            raise

        usage_bytes = getattr(remote, "usage_bytes", None) or getattr(remote, "bytes", 0) or 0
        status = getattr(remote, "status", None) or "ready"

        async with self._session_factory() as session:
            store = VectorStore(
                id=uuid.uuid4(),
                openai_id=remote.id,
                tenant_id=tenant_uuid,
                owner_user_id=owner_uuid,
                name=name,
                description=description,
                status=status,
                usage_bytes=usage_bytes,
                expires_after=expires_after,
                metadata_json=metadata or {},
            )
            session.add(store)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                message = str(exc)
                if (
                    "uq_vector_stores_tenant_name" in message
                    or "vector_stores.tenant_id" in message
                ):
                    await self._safe_delete_remote_store(client, remote.id)
                    raise VectorStoreNameConflictError(
                        "A vector store with this name already exists"
                    ) from exc
                await self._safe_delete_remote_store(client, remote.id)
                raise
            except Exception:
                await session.rollback()
                await self._safe_delete_remote_store(client, remote.id)
                raise
            await session.refresh(store)
            return store

    async def list_stores(
        self, *, tenant_id: uuid.UUID | str, limit: int = 50, offset: int = 0
    ) -> tuple[list[VectorStore], int]:
        tenant_uuid = _coerce_uuid(tenant_id)
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(VectorStore)
                .where(
                    VectorStore.tenant_id == tenant_uuid,
                    VectorStore.deleted_at.is_(None),
                )
            )
            result = await session.scalars(
                select(VectorStore)
                .where(VectorStore.tenant_id == tenant_uuid, VectorStore.deleted_at.is_(None))
                .order_by(VectorStore.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result), int(total or 0)

    async def ensure_primary_store(
        self, *, tenant_id: uuid.UUID | str, owner_user_id: uuid.UUID | str | None = None
    ) -> VectorStore:
        """Idempotently ensure a default 'primary' store exists for the tenant."""

        tenant_uuid = _coerce_uuid(tenant_id)
        owner_uuid = _coerce_uuid_optional(owner_user_id)

        async with self._session_factory() as session:
            existing = await session.scalar(
                select(VectorStore).where(
                    VectorStore.tenant_id == tenant_uuid,
                    VectorStore.name == "primary",
                    VectorStore.deleted_at.is_(None),
                )
            )
            if existing:
                return existing

        return await self.create_store(
            tenant_id=tenant_uuid,
            owner_user_id=owner_uuid,
            name="primary",
            description="Default tenant vector store",
        )

    async def get_store_by_name(
        self, *, tenant_id: uuid.UUID | str, name: str
    ) -> VectorStore | None:
        tenant_uuid = _coerce_uuid(tenant_id)
        async with self._session_factory() as session:
            return await session.scalar(
                select(VectorStore).where(
                    VectorStore.tenant_id == tenant_uuid,
                    VectorStore.name == name,
                    VectorStore.deleted_at.is_(None),
                )
            )

    async def get_store_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_id: str
    ) -> VectorStore | None:
        tenant_uuid = _coerce_uuid(tenant_id)
        async with self._session_factory() as session:
            return await session.scalar(
                select(VectorStore)
                .where(
                    VectorStore.openai_id == openai_id,
                    VectorStore.tenant_id == tenant_uuid,
                    VectorStore.deleted_at.is_(None),
                )
                .limit(1)
            )

    async def get_agent_binding(
        self, *, tenant_id: uuid.UUID | str, agent_key: str
    ) -> VectorStore | None:
        tenant_uuid = _coerce_uuid(tenant_id)
        async with self._session_factory() as session:
            binding = await session.scalar(
                select(AgentVectorStore)
                .where(
                    AgentVectorStore.tenant_id == tenant_uuid,
                    AgentVectorStore.agent_key == agent_key,
                )
                .limit(1)
            )
            if binding is None:
                return None
            store = await session.get(VectorStore, binding.vector_store_id)
            if store is None or store.deleted_at is not None:
                return None
            return store

    async def bind_agent_to_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> AgentVectorStore:
        tenant_uuid = _coerce_uuid(tenant_id)
        store = await self._get_store(vector_store_id, tenant_id=tenant_uuid)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(AgentVectorStore).where(
                    AgentVectorStore.tenant_id == tenant_uuid,
                    AgentVectorStore.agent_key == agent_key,
                )
            )

            if existing:
                if existing.vector_store_id != store.id:
                    existing.vector_store_id = store.id
                    try:
                        await session.commit()
                    except IntegrityError as exc:
                        await session.rollback()
                        raise VectorStoreValidationError(
                            "Failed to rebind agent to vector store"
                        ) from exc
                return existing

            binding = AgentVectorStore(
                agent_key=agent_key,
                vector_store_id=store.id,
                tenant_id=tenant_uuid,
            )
            session.add(binding)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise VectorStoreValidationError("Failed to bind agent to vector store") from exc
            await session.refresh(binding)
            return binding

    async def unbind_agent_from_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> None:
        tenant_uuid = _coerce_uuid(tenant_id)
        store_uuid = _coerce_uuid(vector_store_id)
        async with self._session_factory() as session:
            binding = await session.scalar(
                select(AgentVectorStore).where(
                    AgentVectorStore.tenant_id == tenant_uuid,
                    AgentVectorStore.agent_key == agent_key,
                    AgentVectorStore.vector_store_id == store_uuid,
                )
            )
            if binding is None:
                return
            await session.delete(binding)
            await session.commit()

    async def get_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> VectorStore:
        return await self._get_store(vector_store_id, tenant_id=tenant_id)

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
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)

        # Prevent duplicate attachments before invoking OpenAI
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(VectorStoreFile).where(
                    VectorStoreFile.vector_store_id == vector_store_id,
                    VectorStoreFile.openai_file_id == file_id,
                    VectorStoreFile.deleted_at.is_(None),
                )
            )
            if existing:
                raise VectorStoreFileConflictError("File already attached to this vector store")

        client = self._openai_client(store.tenant_id)

        # Fetch file metadata to persist filename/size
        file_meta = await client.files.retrieve(file_id)

        limits = await self._resolve_limits(store.tenant_id)
        await self._enforce_file_limits(store=store, file_meta=file_meta, limits=limits)

        t0 = perf_counter()
        file_kwargs: dict[str, Any] = {
            "vector_store_id": store.openai_id,
            "file_id": file_id,
        }
        if attributes is not None:
            file_kwargs["attributes"] = attributes
        if chunking_strategy is not None:
            file_kwargs["chunking_strategy"] = chunking_strategy

        try:
            with trace(
                workflow_name="vector_store.attach_file",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                },
            ):
                if poll:
                    remote_file = await client.vector_stores.files.create_and_poll(**file_kwargs)
                else:
                    remote_file = await client.vector_stores.files.create(**file_kwargs)
            self._observe("attach_file", "success", t0)
        except Exception as exc:
            self._observe("attach_file", "error", t0)
            logger.warning(
                "vector_store.attach.failed",
                exc_info=exc,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

        usage_bytes = (
            getattr(remote_file, "usage_bytes", None) or getattr(remote_file, "bytes", 0) or 0
        )
        status = getattr(remote_file, "status", None) or "indexing"

        async with self._session_factory() as session:
            db_file = VectorStoreFile(
                id=uuid.uuid4(),
                openai_file_id=file_id,
                vector_store_id=vector_store_id,
                filename=getattr(file_meta, "filename", file_id),
                mime_type=getattr(file_meta, "mime_type", None),
                size_bytes=getattr(file_meta, "bytes", None),
                usage_bytes=usage_bytes,
                status=status,
                attributes_json=attributes or {},
                chunking_json=chunking_strategy,
                last_error=getattr(remote_file, "last_error", None),
            )
            session.add(db_file)
            # bump store usage if present
            if usage_bytes:
                await session.execute(
                    sa_update(VectorStore)
                    .where(VectorStore.id == vector_store_id)
                    .values(usage_bytes=VectorStore.usage_bytes + usage_bytes)
                )
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                message = str(exc)
                if "uq_vector_store_files_store_file" in message or "vector_store_files" in message:
                    await self._safe_delete_remote_file(client, store.openai_id, file_id)
                    raise VectorStoreFileConflictError(
                        "File already attached to this vector store"
                    ) from exc
                await self._safe_delete_remote_file(client, store.openai_id, file_id)
                raise
            except Exception:
                await session.rollback()
                await self._safe_delete_remote_file(client, store.openai_id, file_id)
                raise
            await session.refresh(db_file)
            return db_file

    async def list_files(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[VectorStoreFile], int]:
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)
        async with self._session_factory() as session:
            conditions = [
                VectorStoreFile.vector_store_id == store.id,
                VectorStoreFile.deleted_at.is_(None),
            ]
            if status:
                conditions.append(VectorStoreFile.status == status)
            total = await session.scalar(
                select(func.count()).select_from(VectorStoreFile).where(*conditions)
            )
            rows = await session.scalars(
                select(VectorStoreFile)
                .where(*conditions)
                .order_by(VectorStoreFile.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(rows), int(total or 0)

    async def get_file(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str, openai_file_id: str
    ) -> VectorStoreFile:
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)
        async with self._session_factory() as session:
            row = await session.scalar(
                select(VectorStoreFile).where(
                    VectorStoreFile.vector_store_id == store.id,
                    VectorStoreFile.openai_file_id == openai_file_id,
                    VectorStoreFile.deleted_at.is_(None),
                )
            )
            if row is None:
                raise VectorStoreNotFoundError(
                    f"File {openai_file_id} not found for vector store {vector_store_id}"
                )
            return row

    async def search(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        query: str,
        filters: dict[str, Any] | None = None,
        max_num_results: int | None = None,
        ranking_options: dict[str, Any] | None = None,
    ) -> Any:
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)
        client = self._openai_client(store.tenant_id)
        kwargs: dict[str, Any] = {"vector_store_id": store.openai_id, "query": query}
        if filters:
            kwargs["filters"] = filters
        if max_num_results:
            kwargs["max_num_results"] = max_num_results
        if ranking_options:
            kwargs["ranking_options"] = ranking_options
        t0 = perf_counter()
        try:
            with trace(
                workflow_name="vector_store.search",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                },
            ):
                result = await client.vector_stores.search(**kwargs)
            self._observe("search", "success", t0)
            return result
        except Exception as exc:
            self._observe("search", "error", t0)
            logger.warning(
                "vector_store.search.failed",
                exc_info=exc,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

    async def delete_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> None:
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)
        client = self._openai_client(store.tenant_id)
        t0 = perf_counter()
        try:
            with trace(
                workflow_name="vector_store.delete_store",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                },
            ):
                await client.vector_stores.delete(store.openai_id)
            self._observe("delete_store", "success", t0)
        except Exception as exc:
            self._observe("delete_store", "error", t0)
            logger.warning(
                "vector_store.delete.failed",
                exc_info=exc,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

        async with self._session_factory() as session:
            db_store = await session.get(VectorStore, vector_store_id)
            if db_store:
                db_store.deleted_at = datetime.now(UTC)
                db_store.status = "deleted"
                await session.commit()

    async def delete_file(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str, file_id: str
    ) -> None:
        store = await self._get_store(vector_store_id, tenant_id=tenant_id)
        client = self._openai_client(store.tenant_id)
        t0 = perf_counter()
        try:
            with trace(
                workflow_name="vector_store.delete_file",
                metadata={
                    "tenant_id": str(store.tenant_id),
                    "vector_store_id": str(store.id),
                    "file_id": file_id,
                },
            ):
                await client.vector_stores.files.delete(
                    vector_store_id=store.openai_id, file_id=file_id
                )
            self._observe("delete_file", "success", t0)
        except Exception as exc:
            self._observe("delete_file", "error", t0)
            logger.warning(
                "vector_store.file_delete.failed",
                exc_info=exc,
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            )
            raise

        async with self._session_factory() as session:
            row = await session.scalar(
                select(VectorStoreFile).where(
                    VectorStoreFile.vector_store_id == vector_store_id,
                    VectorStoreFile.openai_file_id == file_id,
                    VectorStoreFile.deleted_at.is_(None),
                )
            )
            if row is None:
                return
            decrement = row.usage_bytes or row.size_bytes or 0
            row.deleted_at = datetime.now(UTC)
            row.status = "deleted"
            if decrement:
                store_row = await session.get(VectorStore, vector_store_id)
                if store_row:
                    store_row.usage_bytes = max((store_row.usage_bytes or 0) - int(decrement), 0)
            await session.commit()

    # -------- Internal helpers --------
    async def _get_store(
        self, vector_store_id: uuid.UUID | str, *, tenant_id: uuid.UUID | str | None = None
    ) -> VectorStore:
        vector_store_uuid = _coerce_uuid(vector_store_id)
        tenant_uuid = _coerce_uuid_optional(tenant_id)
        async with self._session_factory() as session:
            store = await session.get(VectorStore, vector_store_uuid)
            if store is None or store.deleted_at is not None:
                raise VectorStoreNotFoundError(f"Vector store {vector_store_id} not found")
            if tenant_uuid and store.tenant_id != tenant_uuid:
                raise VectorStoreNotFoundError(f"Vector store {vector_store_id} not found")
            return store

    async def _resolve_limits(self, tenant_id: uuid.UUID) -> VectorLimits:
        if self._limit_resolver:
            return await self._limit_resolver.resolve(str(tenant_id))
        settings = self._settings_factory()
        return VectorLimits(
            max_file_bytes=settings.vector_max_file_mb * 1024 * 1024,
            max_total_bytes=settings.vector_max_total_bytes,
            max_files_per_store=settings.vector_max_files_per_store,
            max_stores_per_tenant=settings.vector_max_stores_per_tenant,
        )

    async def _ensure_unique_name(self, tenant_id: uuid.UUID, name: str) -> None:
        """Fail fast when the tenant already has a store with the same name."""

        async with self._session_factory() as session:
            exists = await session.scalar(
                select(VectorStore.id).where(
                    VectorStore.tenant_id == tenant_id,
                    VectorStore.name == name,
                    VectorStore.deleted_at.is_(None),
                )
            )
        if exists:
            raise VectorStoreNameConflictError("A vector store with this name already exists")

    async def _enforce_store_limit(self, tenant_id: uuid.UUID, limits: VectorLimits) -> None:
        max_stores = limits.max_stores_per_tenant
        if max_stores is None:
            return
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(VectorStore)
                .where(
                    VectorStore.tenant_id == tenant_id,
                    VectorStore.deleted_at.is_(None),
                )
            )
        current = int(count or 0)
        if current >= max_stores:
            raise VectorStoreQuotaError("Maximum vector stores reached for tenant")

    async def _enforce_file_limits(
        self, *, store: VectorStore, file_meta: Any, limits: VectorLimits
    ) -> None:
        max_file_bytes = limits.max_file_bytes
        size_bytes = getattr(file_meta, "bytes", None)
        if size_bytes is not None and size_bytes > max_file_bytes:
            raise VectorStoreValidationError(
                f"File exceeds maximum size of {int(max_file_bytes / 1024 / 1024)} MB"
            )

        mime = getattr(file_meta, "mime_type", None)
        if (
            mime
            and self._settings_factory().vector_allowed_mime_types
            and mime not in self._settings_factory().vector_allowed_mime_types
        ):
            raise VectorStoreValidationError("MIME type not allowed for vector store indexing")

        # per-store file count
        if limits.max_files_per_store is not None:
            async with self._session_factory() as session:
                count = await session.scalar(
                    select(func.count())
                    .select_from(VectorStoreFile)
                    .where(
                        VectorStoreFile.vector_store_id == store.id,
                        VectorStoreFile.deleted_at.is_(None),
                    )
                )
                files_count = int(count or 0)
                if files_count >= limits.max_files_per_store:
                    raise VectorStoreQuotaError("Maximum files reached for this vector store")

        # total bytes cap (tenant-wide) if configured
        if limits.max_total_bytes is not None and size_bytes is not None:
            async with self._session_factory() as session:
                total_bytes = await session.scalar(
                    select(func.coalesce(func.sum(VectorStore.usage_bytes), 0)).where(
                        VectorStore.tenant_id == store.tenant_id,
                        VectorStore.deleted_at.is_(None),
                    )
                )
                projected = (int(total_bytes or 0)) + int(size_bytes)
                if projected > limits.max_total_bytes:
                    raise VectorStoreQuotaError("Tenant vector store byte cap exceeded")

    def _openai_client(self, tenant_id: uuid.UUID | str) -> AsyncOpenAI:
        tenant_uuid = _coerce_uuid(tenant_id)
        settings = self._settings_factory()
        api_key = (
            self._get_tenant_api_key(tenant_uuid, settings)
            if self._get_tenant_api_key
            else settings.openai_api_key
        )
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return AsyncOpenAI(api_key=api_key)

    async def get_file_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_file_id: str
    ) -> VectorStoreFile:
        """Ensure a vector store file belongs to the tenant by OpenAI file id."""

        tenant_uuid = _coerce_uuid(tenant_id)
        async with self._session_factory() as session:
            row = await session.scalar(
                select(VectorStoreFile)
                .join(VectorStore, VectorStore.id == VectorStoreFile.vector_store_id)
                .where(
                    VectorStoreFile.openai_file_id == openai_file_id,
                    VectorStoreFile.deleted_at.is_(None),
                    VectorStore.tenant_id == tenant_uuid,
                    VectorStore.deleted_at.is_(None),
                )
            )

            if row is None:
                raise VectorStoreNotFoundError(
                    f"File {openai_file_id} not found for tenant {tenant_id}"
                )

            return row

    def _observe(self, operation: str, result: str, start_time: float) -> None:
        duration = max(perf_counter() - start_time, 0.0)
        VECTOR_STORE_OPERATIONS_TOTAL.labels(operation=operation, result=result).inc()
        VECTOR_STORE_OPERATION_DURATION_SECONDS.labels(operation=operation, result=result).observe(
            duration
        )

    async def _safe_delete_remote_store(self, client: AsyncOpenAI, remote_id: str) -> None:
        """Best-effort cleanup of remote stores when local persistence fails."""

        try:
            await client.vector_stores.delete(remote_id)
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.warning(
                "vector_store.cleanup_failed",
                exc_info=exc,
                extra={"remote_id": remote_id},
            )

    async def _safe_delete_remote_file(
        self, client: AsyncOpenAI, remote_store_id: str, file_id: str
    ) -> None:
        """Best-effort cleanup of remote files when local persistence fails."""

        try:
            await client.vector_stores.files.delete(
                vector_store_id=remote_store_id, file_id=file_id
            )
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.warning(
                "vector_store.file_cleanup_failed",
                exc_info=exc,
                extra={"remote_store_id": remote_store_id, "file_id": file_id},
            )


_SERVICE_SINGLETON: VectorStoreService | None = None


def get_vector_store_service() -> VectorStoreService:
    global _SERVICE_SINGLETON
    if _SERVICE_SINGLETON is None:
        settings = get_settings()
        _SERVICE_SINGLETON = VectorStoreService(
            get_async_sessionmaker(),
            lambda: settings,
        )
    return _SERVICE_SINGLETON


class _VectorStoreServiceHandle:
    def __getattr__(self, name: str):
        return getattr(get_vector_store_service(), name)


vector_store_service = _VectorStoreServiceHandle()


__all__ = [
    "VectorStoreService",
    "VectorStoreNotFoundError",
    "get_vector_store_service",
    "vector_store_service",
]
