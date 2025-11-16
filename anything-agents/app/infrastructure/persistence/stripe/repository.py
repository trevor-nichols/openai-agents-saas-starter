"""Persistence adapter for Stripe webhook events."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
    StripeEventStatus,
)

__all__ = [
    "StripeEventRepository",
]

logger = logging.getLogger("anything-agents.persistence.stripe_events")


class StripeEventRepository:
    """Store and update Stripe webhook events for auditing & replay."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_event(
        self,
        *,
        stripe_event_id: str,
        event_type: str,
        payload: dict[str, Any],
        tenant_hint: str | None,
        stripe_created_at: datetime | None,
    ) -> tuple[StripeEvent, bool]:
        """Insert the event if it doesn't exist and return (row, created)."""

        async with self._session_factory() as session:
            existing = await session.scalar(
                select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id)
            )
            if existing is not None:
                return existing, False

            entity = StripeEvent(
                id=uuid.uuid4(),
                stripe_event_id=stripe_event_id,
                event_type=event_type,
                payload=payload,
                tenant_hint=tenant_hint,
                stripe_created_at=stripe_created_at,
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity, True

    async def get_by_event_id(self, stripe_event_id: str) -> StripeEvent | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id)
            )

    async def get_event_by_uuid(self, event_uuid: uuid.UUID) -> StripeEvent | None:
        async with self._session_factory() as session:
            return await session.scalar(select(StripeEvent).where(StripeEvent.id == event_uuid))

    async def record_outcome(
        self,
        event_id: uuid.UUID,
        *,
        status: StripeEventStatus,
        error: str | None = None,
    ) -> datetime:
        processed_at = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEvent)
                .where(StripeEvent.id == event_id)
                .values(
                    processed_at=processed_at,
                    processing_outcome=status.value,
                    processing_error=error,
                    processing_attempts=StripeEvent.processing_attempts + 1,
                )
            )
            await session.commit()
        return processed_at

    async def list_processed_events_since(
        self,
        *,
        processed_after: datetime | None,
        limit: int = 500,
    ) -> list[StripeEvent]:
        async with self._session_factory() as session:
            stmt = (
                select(StripeEvent)
                .where(StripeEvent.processing_outcome == StripeEventStatus.PROCESSED.value)
                .where(StripeEvent.processed_at.is_not(None))
                .order_by(StripeEvent.processed_at)
                .limit(limit)
            )
            if processed_after is not None:
                stmt = stmt.where(StripeEvent.processed_at > processed_after)
            result = await session.execute(stmt)
            return list(result.scalars())

    async def list_events(
        self,
        *,
        status: StripeEventStatus | str | None = None,
        limit: int = 20,
    ) -> list[StripeEvent]:
        async with self._session_factory() as session:
            stmt = select(StripeEvent).order_by(StripeEvent.received_at.desc()).limit(limit)
            if status:
                status_value = (
                    status.value if isinstance(status, StripeEventStatus) else str(status)
                )
                stmt = stmt.where(StripeEvent.processing_outcome == status_value)
            result = await session.execute(stmt)
            return list(result.scalars())

    async def list_tenant_events(
        self,
        *,
        tenant_id: str,
        limit: int = 50,
        cursor_received_at: datetime | None = None,
        cursor_event_id: uuid.UUID | None = None,
        event_type: str | None = None,
        status: StripeEventStatus | str | None = None,
    ) -> list[StripeEvent]:
        """Return a tenant-scoped slice of Stripe events ordered by recency."""

        async with self._session_factory() as session:
            stmt = (
                select(StripeEvent)
                .where(StripeEvent.tenant_hint == tenant_id)
                .order_by(StripeEvent.received_at.desc(), StripeEvent.id.desc())
                .limit(max(1, limit))
            )

            if event_type:
                stmt = stmt.where(StripeEvent.event_type == event_type)

            if status:
                status_value = (
                    status.value if isinstance(status, StripeEventStatus) else str(status)
                )
                stmt = stmt.where(StripeEvent.processing_outcome == status_value)

            if cursor_received_at is not None and cursor_event_id is not None:
                stmt = stmt.where(
                    or_(
                        StripeEvent.received_at < cursor_received_at,
                        and_(
                            StripeEvent.received_at == cursor_received_at,
                            StripeEvent.id < cursor_event_id,
                        ),
                    )
                )

            result = await session.execute(stmt)
            return list(result.scalars())

    async def ensure_dispatch(self, *, event_id: uuid.UUID, handler: str) -> StripeEventDispatch:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(StripeEventDispatch)
                .where(StripeEventDispatch.stripe_event_id == event_id)
                .where(StripeEventDispatch.handler == handler)
            )
            if existing is not None:
                return existing

            entity = StripeEventDispatch(
                id=uuid.uuid4(),
                stripe_event_id=event_id,
                handler=handler,
            )
            session.add(entity)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(StripeEventDispatch)
                    .where(StripeEventDispatch.stripe_event_id == event_id)
                    .where(StripeEventDispatch.handler == handler)
                )
                if existing is None:  # pragma: no cover - race condition fallback
                    raise
                return existing
            await session.refresh(entity)
            return entity

    async def get_dispatch(self, dispatch_id: uuid.UUID) -> StripeEventDispatch | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(StripeEventDispatch).where(StripeEventDispatch.id == dispatch_id)
            )

    async def list_dispatches(
        self,
        *,
        handler: str | None = None,
        status: StripeDispatchStatus | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[StripeEventDispatch, StripeEvent]]:
        async with self._session_factory() as session:
            stmt = (
                select(StripeEventDispatch, StripeEvent)
                .join(StripeEvent, StripeEvent.id == StripeEventDispatch.stripe_event_id)
                .order_by(StripeEventDispatch.created_at.desc())
                .offset(max(offset, 0))
                .limit(limit)
            )
            if handler:
                stmt = stmt.where(StripeEventDispatch.handler == handler)
            if status:
                status_value = (
                    status.value if isinstance(status, StripeDispatchStatus) else str(status)
                )
                stmt = stmt.where(StripeEventDispatch.status == status_value)
            result = await session.execute(stmt)
            rows = result.fetchall()
            return [(row[0], row[1]) for row in rows]

    async def mark_dispatch_in_progress(self, dispatch_id: uuid.UUID) -> StripeEventDispatch | None:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEventDispatch)
                .where(StripeEventDispatch.id == dispatch_id)
                .values(
                    status=StripeDispatchStatus.IN_PROGRESS.value,
                    attempts=StripeEventDispatch.attempts + 1,
                    last_attempt_at=now,
                    next_retry_at=None,
                    last_error=None,
                    updated_at=now,
                )
            )
            await session.commit()
        return await self.get_dispatch(dispatch_id)

    async def list_dispatches_for_retry(
        self,
        *,
        limit: int = 25,
        ready_before: datetime | None = None,
    ) -> list[StripeEventDispatch]:
        cutoff = ready_before or datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = (
                select(StripeEventDispatch)
                .where(StripeEventDispatch.status == StripeDispatchStatus.FAILED.value)
                .where(
                    or_(
                        StripeEventDispatch.next_retry_at.is_(None),
                        StripeEventDispatch.next_retry_at <= cutoff,
                    )
                )
                .order_by(
                    StripeEventDispatch.next_retry_at.asc(), StripeEventDispatch.created_at.asc()
                )
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars())

    async def mark_dispatch_completed(self, dispatch_id: uuid.UUID) -> StripeEventDispatch | None:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEventDispatch)
                .where(StripeEventDispatch.id == dispatch_id)
                .values(
                    status=StripeDispatchStatus.COMPLETED.value,
                    last_error=None,
                    next_retry_at=None,
                    updated_at=now,
                )
            )
            await session.commit()
        return await self.get_dispatch(dispatch_id)

    async def mark_dispatch_failed(
        self,
        dispatch_id: uuid.UUID,
        *,
        error: str,
        next_retry_at: datetime | None = None,
    ) -> StripeEventDispatch | None:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEventDispatch)
                .where(StripeEventDispatch.id == dispatch_id)
                .values(
                    status=StripeDispatchStatus.FAILED.value,
                    last_error=error,
                    next_retry_at=next_retry_at,
                    updated_at=now,
                )
            )
            await session.commit()
        return await self.get_dispatch(dispatch_id)

    async def reset_dispatch(self, dispatch_id: uuid.UUID) -> StripeEventDispatch | None:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEventDispatch)
                .where(StripeEventDispatch.id == dispatch_id)
                .values(
                    status=StripeDispatchStatus.PENDING.value,
                    last_error=None,
                    next_retry_at=None,
                    updated_at=now,
                )
            )
            await session.commit()
        return await self.get_dispatch(dispatch_id)


def configure_stripe_event_repository(repository: StripeEventRepository) -> None:
    """Install the provided Stripe event repository in the application container."""

    from app.bootstrap.container import get_container

    get_container().stripe_event_repository = repository


def reset_stripe_event_repository() -> None:
    """Clear the configured repository (used in tests)."""

    from app.bootstrap.container import get_container

    container = get_container()
    container.stripe_event_repository = None


def get_stripe_event_repository() -> StripeEventRepository:
    """Return the configured repository or raise if missing."""

    from app.bootstrap.container import get_container

    repository = get_container().stripe_event_repository
    if repository is None:
        raise RuntimeError(
            "StripeEventRepository is not configured. Ensure ENABLE_BILLING=true on startup."
        )
    return repository
