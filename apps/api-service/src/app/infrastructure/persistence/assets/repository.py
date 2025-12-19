"""Postgres-backed repository for asset catalog metadata."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.assets import AssetRecord, AssetRepository, AssetSourceTool, AssetType, AssetView
from app.infrastructure.persistence.assets.models import AgentAsset
from app.infrastructure.persistence.storage.models import StorageObject


class SqlAlchemyAssetRepository(AssetRepository):
    """Persists and queries asset catalog entries."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, asset: AssetRecord) -> AssetRecord:
        async with self._session_factory() as session:
            row = AgentAsset(
                id=asset.id,
                tenant_id=asset.tenant_id,
                storage_object_id=asset.storage_object_id,
                asset_type=asset.asset_type,
                source_tool=asset.source_tool,
                conversation_id=asset.conversation_id,
                message_id=asset.message_id,
                tool_call_id=asset.tool_call_id,
                response_id=asset.response_id,
                container_id=asset.container_id,
                openai_file_id=asset.openai_file_id,
                metadata_json=asset.metadata or {},
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await self.get_by_storage_object(
                    tenant_id=asset.tenant_id,
                    storage_object_id=asset.storage_object_id,
                )
                if existing is not None:
                    return existing
                raise
            await session.refresh(row)
            return _to_domain(row)

    async def get(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> AssetView | None:
        async with self._session_factory() as session:
            stmt = _base_view_query().where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.id == asset_id,
                AgentAsset.deleted_at.is_(None),
                StorageObject.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                return None
            asset_row, storage_row = row
            return _to_view(asset_row, storage_row)

    async def get_record(
        self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID
    ) -> AssetRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentAsset).where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.id == asset_id,
                AgentAsset.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return _to_domain(row) if row else None

    async def get_by_storage_object(
        self, *, tenant_id: uuid.UUID, storage_object_id: uuid.UUID
    ) -> AssetRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentAsset).where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.storage_object_id == storage_object_id,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return _to_domain(row) if row else None

    async def list(
        self,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        asset_type: AssetType | None = None,
        source_tool: AssetSourceTool | None = None,
        conversation_id: uuid.UUID | None = None,
        message_id: int | None = None,
        agent_key: str | None = None,
        mime_type_prefix: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[AssetView]:
        async with self._session_factory() as session:
            stmt = _base_view_query().where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.deleted_at.is_(None),
                StorageObject.deleted_at.is_(None),
            )
            stmt = _apply_filters(
                stmt,
                asset_type=asset_type,
                source_tool=source_tool,
                conversation_id=conversation_id,
                message_id=message_id,
                agent_key=agent_key,
                mime_type_prefix=mime_type_prefix,
                created_after=created_after,
                created_before=created_before,
            )
            stmt = stmt.order_by(AgentAsset.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            rows = result.fetchall()
            return [_to_view(asset_row, storage_row) for asset_row, storage_row in rows]

    async def mark_deleted(self, *, tenant_id: uuid.UUID, asset_id: uuid.UUID) -> None:
        async with self._session_factory() as session:
            stmt = select(AgentAsset).where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.id == asset_id,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return
            row.deleted_at = row.deleted_at or datetime.utcnow()
            session.add(row)
            await session.commit()

    async def link_message(
        self,
        *,
        tenant_id: uuid.UUID,
        message_id: int,
        storage_object_ids: Sequence[uuid.UUID],
    ) -> int:
        if not storage_object_ids:
            return 0
        async with self._session_factory() as session:
            stmt = select(AgentAsset).where(
                AgentAsset.tenant_id == tenant_id,
                AgentAsset.storage_object_id.in_(storage_object_ids),
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            if not rows:
                return 0
            for row in rows:
                if row.message_id is None:
                    row.message_id = message_id
                    session.add(row)
            await session.commit()
            return len(rows)


def _base_view_query() -> Select[tuple[AgentAsset, StorageObject]]:
    return select(AgentAsset, StorageObject).join(
        StorageObject, AgentAsset.storage_object_id == StorageObject.id
    )


def _apply_filters(
    stmt: Select[tuple[AgentAsset, StorageObject]],
    *,
    asset_type: AssetType | None,
    source_tool: AssetSourceTool | None,
    conversation_id: uuid.UUID | None,
    message_id: int | None,
    agent_key: str | None,
    mime_type_prefix: str | None,
    created_after: datetime | None,
    created_before: datetime | None,
) -> Select[tuple[AgentAsset, StorageObject]]:
    filters: list[Any] = []
    if asset_type:
        filters.append(AgentAsset.asset_type == asset_type)
    if source_tool:
        filters.append(AgentAsset.source_tool == source_tool)
    if conversation_id:
        filters.append(AgentAsset.conversation_id == conversation_id)
    if message_id:
        filters.append(AgentAsset.message_id == message_id)
    if agent_key:
        filters.append(StorageObject.agent_key == agent_key)
    if mime_type_prefix:
        filters.append(StorageObject.mime_type.ilike(f"{mime_type_prefix}%"))
    if created_after:
        filters.append(AgentAsset.created_at >= created_after)
    if created_before:
        filters.append(AgentAsset.created_at <= created_before)
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt


def _to_domain(row: AgentAsset) -> AssetRecord:
    return AssetRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        storage_object_id=row.storage_object_id,
        asset_type=row.asset_type,  # type: ignore[arg-type]
        source_tool=row.source_tool,  # type: ignore[arg-type]
        conversation_id=row.conversation_id,
        message_id=row.message_id,
        tool_call_id=row.tool_call_id,
        response_id=row.response_id,
        container_id=row.container_id,
        openai_file_id=row.openai_file_id,
        metadata=row.metadata_json or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        deleted_at=row.deleted_at,
    )


def _to_view(asset_row: AgentAsset, storage_row: StorageObject) -> AssetView:
    return AssetView(
        asset=_to_domain(asset_row),
        filename=storage_row.filename,
        mime_type=storage_row.mime_type,
        size_bytes=storage_row.size_bytes,
        agent_key=storage_row.agent_key,
        storage_status=storage_row.status,
        storage_created_at=storage_row.created_at,
    )


__all__ = ["SqlAlchemyAssetRepository"]
