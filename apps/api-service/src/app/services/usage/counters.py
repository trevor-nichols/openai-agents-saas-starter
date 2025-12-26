"""Tenant/user usage aggregation service."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.usage.models import UsageCounter, UsageCounterGranularity


class UsageCounterService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def increment(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        period_start: date,
        granularity: UsageCounterGranularity,
        input_tokens: int = 0,
        output_tokens: int = 0,
        requests: int = 0,
        storage_bytes: int = 0,
    ) -> None:
        async with self._session_factory() as session:
            now = datetime.now(UTC)
            insert_fn = self._insert_for_dialect(session)
            stmt = insert_fn(UsageCounter).values(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                period_start=period_start,
                granularity=granularity,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                requests=int(requests),
                storage_bytes=int(storage_bytes),
                created_at=now,
                updated_at=now,
            )
            update_values = {
                "input_tokens": UsageCounter.input_tokens + stmt.excluded.input_tokens,
                "output_tokens": UsageCounter.output_tokens + stmt.excluded.output_tokens,
                "requests": UsageCounter.requests + stmt.excluded.requests,
                "storage_bytes": UsageCounter.storage_bytes + stmt.excluded.storage_bytes,
                "updated_at": now,
            }

            if user_id is None:
                stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        UsageCounter.tenant_id,
                        UsageCounter.period_start,
                        UsageCounter.granularity,
                    ],
                    index_where=UsageCounter.user_id.is_(None),
                    set_=update_values,
                )
            else:
                stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        UsageCounter.tenant_id,
                        UsageCounter.user_id,
                        UsageCounter.period_start,
                        UsageCounter.granularity,
                    ],
                    set_=update_values,
                )
            await session.execute(stmt)
            await session.commit()

    async def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        limit: int = 50,
        before: date | None = None,
    ) -> list[UsageCounter]:
        query: Select[tuple[UsageCounter]] = select(UsageCounter).where(
            UsageCounter.tenant_id == tenant_id
        )
        if before:
            query = query.where(UsageCounter.period_start < before)
        query = query.order_by(UsageCounter.period_start.desc()).limit(limit)
        async with self._session_factory() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def _insert_for_dialect(session: AsyncSession):  # pragma: no cover - trivial
        dialect = session.bind.dialect.name if session.bind else "postgresql"
        if dialect == "sqlite":
            return sqlite_insert
        return pg_insert


def get_usage_counter_service() -> UsageCounterService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    session_factory = container.session_factory or get_async_sessionmaker()
    container.session_factory = session_factory
    if container.usage_counter_service is None:
        container.usage_counter_service = UsageCounterService(session_factory)
    return container.usage_counter_service


__all__ = ["UsageCounterService", "get_usage_counter_service"]
