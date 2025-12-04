"""SQLAlchemy implementation of per-user activity inbox receipts/checkpoints."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.activity import (
    ActivityInboxRepository,
    ActivityLastSeen,
    ActivityReceipt,
    ReceiptStatus,
)
from app.infrastructure.persistence.activity.models import (
    ActivityEventRow,
    ActivityLastSeenRow,
    ActivityReceiptRow,
)


def _now() -> datetime:
    return datetime.now(UTC)


class SqlAlchemyActivityInboxRepository(ActivityInboxRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def upsert_receipt(
        self,
        *,
        tenant_id: str,
        user_id: str,
        event_id: str,
        status: ReceiptStatus,
    ) -> ActivityReceipt:
        tenant_uuid = uuid.UUID(tenant_id)
        user_uuid = uuid.UUID(user_id)
        event_uuid = uuid.UUID(event_id)
        now = _now()

        async with self._session_factory() as session:
            row = await session.scalar(
                select(ActivityReceiptRow).where(
                    ActivityReceiptRow.tenant_id == tenant_uuid,
                    ActivityReceiptRow.user_id == user_uuid,
                    ActivityReceiptRow.event_id == event_uuid,
                ).limit(1)
            )
            if row:
                row.status = status
                row.updated_at = now
            else:
                row = ActivityReceiptRow(
                    tenant_id=tenant_uuid,
                    user_id=user_uuid,
                    event_id=event_uuid,
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            await session.commit()

        return ActivityReceipt(
            tenant_id=tenant_id,
            user_id=user_id,
            event_id=event_id,
            status=status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def fetch_receipts(
        self, *, tenant_id: str, user_id: str, event_ids: Sequence[str]
    ) -> dict[str, ActivityReceipt]:
        if not event_ids:
            return {}
        tenant_uuid = uuid.UUID(tenant_id)
        user_uuid = uuid.UUID(user_id)
        event_uuid_list = [uuid.UUID(eid) for eid in event_ids]

        stmt = select(ActivityReceiptRow).where(
            ActivityReceiptRow.tenant_id == tenant_uuid,
            ActivityReceiptRow.user_id == user_uuid,
            ActivityReceiptRow.event_id.in_(event_uuid_list),
        )
        async with self._session_factory() as session:
            rows = list((await session.execute(stmt)).scalars().all())

        return {
            str(row.event_id): ActivityReceipt(
                tenant_id=tenant_id,
                user_id=user_id,
                event_id=str(row.event_id),
                status=cast(ReceiptStatus, row.status),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        }

    async def upsert_checkpoint(
        self,
        *,
        tenant_id: str,
        user_id: str,
        last_seen_created_at: datetime,
        last_seen_event_id: str | None,
    ) -> ActivityLastSeen:
        tenant_uuid = uuid.UUID(tenant_id)
        user_uuid = uuid.UUID(user_id)
        now = _now()

        async with self._session_factory() as session:
            row = await session.scalar(
                select(ActivityLastSeenRow).where(
                    ActivityLastSeenRow.tenant_id == tenant_uuid,
                    ActivityLastSeenRow.user_id == user_uuid,
                ).limit(1)
            )
            if row:
                row.last_seen_created_at = last_seen_created_at
                row.last_seen_event_id = (
                    uuid.UUID(last_seen_event_id) if last_seen_event_id else None
                )
                row.updated_at = now
            else:
                row = ActivityLastSeenRow(
                    tenant_id=tenant_uuid,
                    user_id=user_uuid,
                    last_seen_created_at=last_seen_created_at,
                    last_seen_event_id=(
                        uuid.UUID(last_seen_event_id) if last_seen_event_id else None
                    ),
                    updated_at=now,
                )
                session.add(row)
            await session.commit()

        return ActivityLastSeen(
            tenant_id=tenant_id,
            user_id=user_id,
            last_seen_created_at=row.last_seen_created_at,
            last_seen_event_id=str(row.last_seen_event_id) if row.last_seen_event_id else None,
            updated_at=row.updated_at,
        )

    async def get_checkpoint(self, *, tenant_id: str, user_id: str) -> ActivityLastSeen | None:
        tenant_uuid = uuid.UUID(tenant_id)
        user_uuid = uuid.UUID(user_id)

        async with self._session_factory() as session:
            row = await session.scalar(
                select(ActivityLastSeenRow).where(
                    ActivityLastSeenRow.tenant_id == tenant_uuid,
                    ActivityLastSeenRow.user_id == user_uuid,
                ).limit(1)
            )

        if not row:
            return None
        return ActivityLastSeen(
            tenant_id=tenant_id,
            user_id=user_id,
            last_seen_created_at=row.last_seen_created_at,
            last_seen_event_id=str(row.last_seen_event_id) if row.last_seen_event_id else None,
            updated_at=row.updated_at,
        )

    async def count_unread_since(
        self,
        *,
        tenant_id: str,
        user_id: str,
        last_seen_created_at: datetime | None,
        last_seen_event_id: str | None,
    ) -> int:
        tenant_uuid = uuid.UUID(tenant_id)
        user_uuid = uuid.UUID(user_id)
        last_seen_uuid = uuid.UUID(last_seen_event_id) if last_seen_event_id else None

        time_clause = None
        if last_seen_created_at:
            # Order by created_at then id to mirror keyset pagination semantics.
            if last_seen_uuid:
                time_clause = or_(
                    ActivityEventRow.created_at > last_seen_created_at,
                    and_(
                        ActivityEventRow.created_at == last_seen_created_at,
                        ActivityEventRow.id > last_seen_uuid,
                    ),
                )
            else:
                time_clause = ActivityEventRow.created_at > last_seen_created_at

        receipts_subq = (
            select(ActivityReceiptRow.event_id)
            .where(
                ActivityReceiptRow.tenant_id == tenant_uuid,
                ActivityReceiptRow.user_id == user_uuid,
                ActivityReceiptRow.status.in_(("read", "dismissed")),
            )
            .subquery()
        )

        where_clauses = [
            ActivityEventRow.tenant_id == tenant_uuid,
            ~ActivityEventRow.id.in_(select(receipts_subq.c.event_id)),
        ]
        if time_clause is not None:
            where_clauses.append(time_clause)

        stmt = (
            select(func.count())
            .select_from(ActivityEventRow)
            .where(*where_clauses)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return int(result.scalar_one())
