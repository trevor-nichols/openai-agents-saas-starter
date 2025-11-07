"""Unit tests for the Stripe event repository."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.stripe.models import StripeEvent
from app.infrastructure.persistence.stripe.repository import (
    StripeEventRepository,
    StripeEventStatus,
)

# Import other model modules so SQLAlchemy's registry resolves relationships during configuration.
import app.infrastructure.persistence.conversations.models  # noqa: F401
import app.infrastructure.persistence.auth.models  # noqa: F401


@pytest.fixture
async def stripe_event_repo():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(StripeEvent.__table__.create)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repository = StripeEventRepository(session_factory)
    try:
        yield repository
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_upsert_event_is_idempotent(stripe_event_repo: StripeEventRepository):
    payload = {"id": "evt_test", "type": "customer.subscription.created"}
    record, created = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_test",
        event_type="customer.subscription.created",
        payload=payload,
        tenant_hint="tenant-123",
        stripe_created_at=datetime.now(timezone.utc),
    )
    assert created is True

    duplicate, created_again = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_test",
        event_type="customer.subscription.created",
        payload=payload,
        tenant_hint="tenant-123",
        stripe_created_at=datetime.now(timezone.utc),
    )
    assert created_again is False
    assert duplicate.id == record.id


@pytest.mark.asyncio
async def test_record_outcome_updates_status(stripe_event_repo: StripeEventRepository):
    payload = {"id": "evt_status", "type": "invoice.paid"}
    record, _ = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_status",
        event_type="invoice.paid",
        payload=payload,
        tenant_hint=None,
        stripe_created_at=None,
    )

    await stripe_event_repo.record_outcome(record.id, status=StripeEventStatus.PROCESSED)
    stored = await stripe_event_repo.get_by_event_id("evt_status")
    assert stored is not None
    assert stored.processing_outcome == StripeEventStatus.PROCESSED.value
