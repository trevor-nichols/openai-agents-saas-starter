"""Postgres-backed repository for storage metadata."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.infrastructure.persistence.storage.models import StorageBucket, StorageObject


class StorageRepository:
    """Persists storage buckets and objects."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_or_create_bucket(
        self,
        *,
        tenant_id: uuid.UUID,
        provider: str,
        bucket_name: str,
        region: str | None,
        prefix: str | None,
    ) -> StorageBucket:
        async with self._session_factory() as session:
            stmt = select(StorageBucket).where(
                StorageBucket.tenant_id == tenant_id,
                StorageBucket.bucket_name == bucket_name,
            )
            result = await session.execute(stmt)
            bucket = result.scalar_one_or_none()
            if bucket:
                return bucket

            bucket = StorageBucket(
                tenant_id=tenant_id,
                provider=provider,
                bucket_name=bucket_name,
                region=region,
                prefix=prefix,
                is_default=True,
                status="ready",
            )
            session.add(bucket)
            await session.commit()
            await session.refresh(bucket)
            return bucket

    async def create_object(
        self,
        *,
        tenant_id: uuid.UUID,
        bucket: StorageBucket,
        object_id: uuid.UUID,
        object_key: str,
        filename: str,
        mime_type: str | None,
        size_bytes: int | None,
        checksum_sha256: str | None,
        status: str,
        created_by_user_id: uuid.UUID | None,
        agent_key: str | None,
        conversation_id: uuid.UUID | None,
        metadata_json: dict[str, Any],
        expires_at,
    ) -> StorageObject:
        async with self._session_factory() as session:
            obj = StorageObject(
                id=object_id,
                tenant_id=tenant_id,
                bucket_id=bucket.id,
                object_key=object_key,
                filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                checksum_sha256=checksum_sha256,
                status=status,
                created_by_user_id=created_by_user_id,
                agent_key=agent_key,
                conversation_id=conversation_id,
                metadata_json=metadata_json,
                expires_at=expires_at,
            )
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def get_object_for_tenant(
        self, *, tenant_id: uuid.UUID, object_id: uuid.UUID
    ) -> StorageObject | None:
        async with self._session_factory() as session:
            stmt = (
                select(StorageObject)
                .options(selectinload(StorageObject.bucket))
                .where(
                    StorageObject.id == object_id,
                    StorageObject.tenant_id == tenant_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_objects(
        self,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        conversation_id: uuid.UUID | None = None,
    ) -> list[StorageObject]:
        async with self._session_factory() as session:
            stmt = (
                select(StorageObject)
                .options(selectinload(StorageObject.bucket))
                .where(
                    StorageObject.tenant_id == tenant_id,
                    StorageObject.deleted_at.is_(None),
                )
                .order_by(StorageObject.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            if conversation_id:
                stmt = stmt.where(StorageObject.conversation_id == conversation_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def mark_deleted(self, *, object_id: uuid.UUID) -> None:
        async with self._session_factory() as session:
            stmt = select(StorageObject).where(StorageObject.id == object_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj is None:
                return
            obj.deleted_at = obj.deleted_at or datetime.utcnow()
            obj.status = "deleted"
            session.add(obj)
            await session.commit()


__all__ = ["StorageRepository"]
