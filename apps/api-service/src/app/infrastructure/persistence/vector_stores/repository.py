"""SQLAlchemy implementations of vector store repository contracts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.vector_stores import (
    AgentVectorStoreBinding,
    AgentVectorStoreRepository,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileRepository,
    VectorStoreRepository,
)
from app.infrastructure.persistence.vector_stores import models


def _to_domain_store(row: models.VectorStore) -> VectorStore:
    return VectorStore(
        id=row.id,
        openai_id=row.openai_id,
        tenant_id=row.tenant_id,
        owner_user_id=row.owner_user_id,
        name=row.name,
        description=row.description,
        status=row.status,
        usage_bytes=row.usage_bytes,
        expires_after=row.expires_after,
        expires_at=row.expires_at,
        last_active_at=row.last_active_at,
        metadata=row.metadata_json or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        deleted_at=row.deleted_at,
    )


def _to_domain_file(row: models.VectorStoreFile) -> VectorStoreFile:
    return VectorStoreFile(
        id=row.id,
        openai_file_id=row.openai_file_id,
        vector_store_id=row.vector_store_id,
        filename=row.filename,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        usage_bytes=row.usage_bytes,
        status=row.status,
        attributes=row.attributes_json or {},
        chunking=row.chunking_json,
        last_error=row.last_error,
        created_at=row.created_at,
        updated_at=row.updated_at,
        deleted_at=row.deleted_at,
    )


class SqlAlchemyVectorStoreRepository(VectorStoreRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def create(self, store: VectorStore) -> VectorStore:
        async with self._session_factory() as session:
            row = models.VectorStore(
                id=store.id,
                openai_id=store.openai_id,
                tenant_id=store.tenant_id,
                owner_user_id=store.owner_user_id,
                name=store.name,
                description=store.description,
                status=store.status,
                usage_bytes=store.usage_bytes,
                expires_after=store.expires_after,
                expires_at=store.expires_at,
                last_active_at=store.last_active_at,
                metadata_json=store.metadata,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            await session.refresh(row)
            return _to_domain_store(row)

    async def list(
        self, *, tenant_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[VectorStore], int]:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(models.VectorStore)
                .where(
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
            )
            rows = await session.scalars(
                select(models.VectorStore)
                .where(
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
                .order_by(models.VectorStore.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return [
                _to_domain_store(row) for row in rows
            ], int(total or 0)

    async def get(self, store_id: uuid.UUID) -> VectorStore | None:
        async with self._session_factory() as session:
            row = await session.get(models.VectorStore, store_id)
            if row is None or row.deleted_at is not None:
                return None
            return _to_domain_store(row)

    async def get_by_name(self, *, tenant_id: uuid.UUID, name: str) -> VectorStore | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.VectorStore).where(
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.name == name,
                    models.VectorStore.deleted_at.is_(None),
                )
            )
            return _to_domain_store(row) if row else None

    async def get_by_openai_id(self, *, tenant_id: uuid.UUID, openai_id: str) -> VectorStore | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.VectorStore)
                .where(
                    models.VectorStore.openai_id == openai_id,
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
                .limit(1)
            )
            return _to_domain_store(row) if row else None

    async def soft_delete(self, store_id: uuid.UUID) -> None:
        async with self._session_factory() as session:
            row = await session.get(models.VectorStore, store_id)
            if row is None:
                return
            row.deleted_at = datetime.now(timezone.utc)  # noqa: UP017
            row.status = "deleted"
            await session.commit()

    async def count_active(self, *, tenant_id: uuid.UUID) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(models.VectorStore)
                .where(
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
            )
            return int(count or 0)

    async def increment_usage(self, *, store_id: uuid.UUID, delta: int) -> None:
        if delta == 0:
            return
        async with self._session_factory() as session:
            await session.execute(
                update(models.VectorStore)
                .where(models.VectorStore.id == store_id)
                .values(usage_bytes=models.VectorStore.usage_bytes + int(delta))
            )
            await session.commit()

    async def sum_usage(self, *, tenant_id: uuid.UUID) -> int:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.coalesce(func.sum(models.VectorStore.usage_bytes), 0)).where(
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
            )
            return int(total or 0)


class SqlAlchemyVectorStoreFileRepository(VectorStoreFileRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def create(self, file: VectorStoreFile) -> VectorStoreFile:
        async with self._session_factory() as session:
            row = models.VectorStoreFile(
                id=file.id,
                openai_file_id=file.openai_file_id,
                vector_store_id=file.vector_store_id,
                filename=file.filename,
                mime_type=file.mime_type,
                size_bytes=file.size_bytes,
                usage_bytes=file.usage_bytes,
                status=file.status,
                attributes_json=file.attributes,
                chunking_json=file.chunking,
                last_error=file.last_error,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            await session.refresh(row)
            return _to_domain_file(row)

    async def list(
        self, *, store_id: uuid.UUID, status: str | None, limit: int, offset: int
    ) -> tuple[list[VectorStoreFile], int]:
        async with self._session_factory() as session:
            conditions = [
                models.VectorStoreFile.vector_store_id == store_id,
                models.VectorStoreFile.deleted_at.is_(None),
            ]
            if status:
                conditions.append(models.VectorStoreFile.status == status)
            total = await session.scalar(
                select(func.count()).select_from(models.VectorStoreFile).where(*conditions)
            )
            rows = await session.scalars(
                select(models.VectorStoreFile)
                .where(*conditions)
                .order_by(models.VectorStoreFile.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return [_to_domain_file(row) for row in rows], int(total or 0)

    async def get(self, *, store_id: uuid.UUID, openai_file_id: str) -> VectorStoreFile | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.VectorStoreFile).where(
                    models.VectorStoreFile.vector_store_id == store_id,
                    models.VectorStoreFile.openai_file_id == openai_file_id,
                    models.VectorStoreFile.deleted_at.is_(None),
                )
            )
            return _to_domain_file(row) if row else None

    async def soft_delete(
        self, *, store_id: uuid.UUID, openai_file_id: str
    ) -> VectorStoreFile | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.VectorStoreFile).where(
                    models.VectorStoreFile.vector_store_id == store_id,
                    models.VectorStoreFile.openai_file_id == openai_file_id,
                    models.VectorStoreFile.deleted_at.is_(None),
                )
            )
            if row is None:
                return None
            row.deleted_at = datetime.now(timezone.utc)  # noqa: UP017
            row.status = "deleted"
            await session.commit()
            await session.refresh(row)
            return _to_domain_file(row)

    async def count_active(self, *, store_id: uuid.UUID) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(models.VectorStoreFile)
                .where(
                    models.VectorStoreFile.vector_store_id == store_id,
                    models.VectorStoreFile.deleted_at.is_(None),
                )
            )
            return int(count or 0)

    async def get_by_openai_id_for_tenant(
        self, *, tenant_id: uuid.UUID, openai_file_id: str
    ) -> VectorStoreFile | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.VectorStoreFile)
                .join(
                    models.VectorStore,
                    models.VectorStore.id == models.VectorStoreFile.vector_store_id,
                )
                .where(
                    models.VectorStoreFile.openai_file_id == openai_file_id,
                    models.VectorStoreFile.deleted_at.is_(None),
                    models.VectorStore.tenant_id == tenant_id,
                    models.VectorStore.deleted_at.is_(None),
                )
            )
            return _to_domain_file(row) if row else None


class SqlAlchemyAgentVectorStoreRepository(AgentVectorStoreRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get_binding(
        self, *, tenant_id: uuid.UUID, agent_key: str
    ) -> AgentVectorStoreBinding | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.AgentVectorStore).where(
                    models.AgentVectorStore.tenant_id == tenant_id,
                    models.AgentVectorStore.agent_key == agent_key,
                )
            )
            if row is None:
                return None
            return AgentVectorStoreBinding(
                agent_key=row.agent_key,
                vector_store_id=row.vector_store_id,
                tenant_id=row.tenant_id,
            )

    async def upsert_binding(self, binding: AgentVectorStoreBinding) -> AgentVectorStoreBinding:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.AgentVectorStore).where(
                    models.AgentVectorStore.tenant_id == binding.tenant_id,
                    models.AgentVectorStore.agent_key == binding.agent_key,
                )
            )
            if row:
                row.vector_store_id = binding.vector_store_id
            else:
                row = models.AgentVectorStore(
                    agent_key=binding.agent_key,
                    vector_store_id=binding.vector_store_id,
                    tenant_id=binding.tenant_id,
                )
                session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            await session.refresh(row)
            return AgentVectorStoreBinding(
                agent_key=row.agent_key,
                vector_store_id=row.vector_store_id,
                tenant_id=row.tenant_id,
            )

    async def delete_binding(
        self, *, tenant_id: uuid.UUID, agent_key: str, vector_store_id: uuid.UUID
    ) -> None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(models.AgentVectorStore).where(
                    models.AgentVectorStore.tenant_id == tenant_id,
                    models.AgentVectorStore.agent_key == agent_key,
                    models.AgentVectorStore.vector_store_id == vector_store_id,
                )
            )
            if row is None:
                return
            await session.delete(row)
            await session.commit()


__all__ = [
    "SqlAlchemyVectorStoreRepository",
    "SqlAlchemyVectorStoreFileRepository",
    "SqlAlchemyAgentVectorStoreRepository",
]
