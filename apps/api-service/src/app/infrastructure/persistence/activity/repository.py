"""SQLAlchemy implementation of the activity event repository."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.activity import (
    ActivityEvent,
    ActivityEventFilters,
    ActivityEventPage,
    ActivityEventRepository,
)
from app.infrastructure.persistence.activity.models import ActivityEventRow


def _encode_cursor(created_at: datetime, row_id: uuid.UUID) -> str:
    payload = f"{created_at.isoformat()}::{row_id}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    created_str, id_str = decoded.split("::", maxsplit=1)
    return datetime.fromisoformat(created_str), uuid.UUID(id_str)


class SqlAlchemyActivityEventRepository(ActivityEventRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def record(self, event: ActivityEvent) -> None:
        row = ActivityEventRow(
            id=uuid.UUID(event.id),
            tenant_id=uuid.UUID(event.tenant_id),
            action=event.action,
            created_at=event.created_at,
            actor_id=uuid.UUID(event.actor_id) if event.actor_id else None,
            actor_type=event.actor_type,
            actor_role=event.actor_role,
            object_type=event.object_type,
            object_id=event.object_id,
            object_name=event.object_name,
            status=event.status,
            source=event.source,
            request_id=event.request_id,
            ip_hash=event.ip_hash,
            user_agent=event.user_agent,
            metadata_json=(
                json.loads(json.dumps(event.metadata)) if event.metadata is not None else None
            ),
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage:
        limit = max(1, min(limit, 200))
        tenant_uuid = uuid.UUID(tenant_id)
        filters = filters or ActivityEventFilters()

        stmt: Select[Any] = select(ActivityEventRow).where(
            ActivityEventRow.tenant_id == tenant_uuid
        )

        if filters.action:
            stmt = stmt.where(ActivityEventRow.action == filters.action)
        if filters.actor_id:
            stmt = stmt.where(ActivityEventRow.actor_id == uuid.UUID(filters.actor_id))
        if filters.object_type:
            stmt = stmt.where(ActivityEventRow.object_type == filters.object_type)
        if filters.object_id:
            stmt = stmt.where(ActivityEventRow.object_id == filters.object_id)
        if filters.status:
            stmt = stmt.where(ActivityEventRow.status == filters.status)
        if filters.request_id:
            stmt = stmt.where(ActivityEventRow.request_id == filters.request_id)
        if filters.created_after:
            stmt = stmt.where(ActivityEventRow.created_at >= filters.created_after)
        if filters.created_before:
            stmt = stmt.where(ActivityEventRow.created_at <= filters.created_before)

        if cursor:
            cursor_created, cursor_id = _decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    ActivityEventRow.created_at < cursor_created,
                    and_(
                        ActivityEventRow.created_at == cursor_created,
                        ActivityEventRow.id < cursor_id,
                    ),
                )
            )

        stmt = (
            stmt.order_by(desc(ActivityEventRow.created_at), desc(ActivityEventRow.id))
            .limit(limit + 1)
        )

        async with self._session_factory() as session:
            rows = list((await session.execute(stmt)).scalars().all())

        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            tail = rows[-1]
            next_cursor = _encode_cursor(tail.created_at, tail.id)

        items = [
            ActivityEvent(
                id=str(row.id),
                tenant_id=str(row.tenant_id),
                action=row.action,
                created_at=row.created_at,
                actor_id=str(row.actor_id) if row.actor_id else None,
                actor_type=row.actor_type,
                actor_role=row.actor_role,
                object_type=row.object_type,
                object_id=row.object_id,
                object_name=row.object_name,
                status=row.status,
                source=row.source,
                request_id=row.request_id,
                ip_hash=row.ip_hash,
                user_agent=row.user_agent,
                metadata=row.metadata_json,
            )
            for row in rows
        ]
        return ActivityEventPage(items=items, next_cursor=next_cursor)


__all__ = ["SqlAlchemyActivityEventRepository"]
