"""Persistence adapter for Stripe webhook events."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventStatus

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
        payload: dict,
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

    async def record_outcome(
        self,
        event_id: uuid.UUID,
        *,
        status: StripeEventStatus,
        error: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(StripeEvent)
                .where(StripeEvent.id == event_id)
                .values(
                    processed_at=datetime.now(timezone.utc),
                    processing_outcome=status.value,
                    processing_error=error,
                    processing_attempts=StripeEvent.processing_attempts + 1,
                )
            )
            await session.commit()


_stripe_event_repository: StripeEventRepository | None = None


def configure_stripe_event_repository(repository: StripeEventRepository) -> None:
    global _stripe_event_repository
    _stripe_event_repository = repository


def reset_stripe_event_repository() -> None:
    global _stripe_event_repository
    _stripe_event_repository = None


def get_stripe_event_repository() -> StripeEventRepository:
    if _stripe_event_repository is None:
        raise RuntimeError("StripeEventRepository is not configured. Ensure ENABLE_BILLING=true on startup.")
    return _stripe_event_repository
