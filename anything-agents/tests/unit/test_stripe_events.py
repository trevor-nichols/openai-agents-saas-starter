"""Unit tests for the Stripe event repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
)
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
        await conn.run_sync(StripeEventDispatch.__table__.create)
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


@pytest.mark.asyncio
async def test_ensure_dispatch_creates_once(stripe_event_repo: StripeEventRepository):
    record, _ = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_dispatch",
        event_type="customer.subscription.created",
        payload={"id": "evt_dispatch"},
        tenant_hint="tenant-1",
        stripe_created_at=None,
    )

    first = await stripe_event_repo.ensure_dispatch(event_id=record.id, handler="billing_sync")
    again = await stripe_event_repo.ensure_dispatch(event_id=record.id, handler="billing_sync")

    assert first.id == again.id
    assert first.status == StripeDispatchStatus.PENDING.value


@pytest.mark.asyncio
async def test_mark_dispatch_flow(stripe_event_repo: StripeEventRepository):
    record, _ = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_flow",
        event_type="customer.subscription.updated",
        payload={"id": "evt_flow"},
        tenant_hint="tenant-1",
        stripe_created_at=None,
    )
    dispatch = await stripe_event_repo.ensure_dispatch(event_id=record.id, handler="billing_sync")

    in_progress = await stripe_event_repo.mark_dispatch_in_progress(dispatch.id)
    assert in_progress is not None
    assert in_progress.status == StripeDispatchStatus.IN_PROGRESS.value

    completed = await stripe_event_repo.mark_dispatch_completed(dispatch.id)
    assert completed is not None
    assert completed.status == StripeDispatchStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_list_dispatches_supports_offset(stripe_event_repo: StripeEventRepository):
    records = []
    for idx in range(3):
        record, _ = await stripe_event_repo.upsert_event(
            stripe_event_id=f"evt_page_{idx}",
            event_type="customer.subscription.created",
            payload={"id": f"evt_page_{idx}"},
            tenant_hint=f"tenant-{idx}",
            stripe_created_at=None,
        )
        await stripe_event_repo.ensure_dispatch(event_id=record.id, handler="billing_sync")
        records.append(record)

    page_two = await stripe_event_repo.list_dispatches(handler="billing_sync", status=None, limit=1, offset=1)
    assert len(page_two) == 1


@pytest.mark.asyncio
async def test_list_dispatches_for_retry_filters_ready_rows(stripe_event_repo: StripeEventRepository):
    record, _ = await stripe_event_repo.upsert_event(
        stripe_event_id="evt_retry",
        event_type="customer.subscription.updated",
        payload={"id": "evt_retry"},
        tenant_hint="tenant-retry",
        stripe_created_at=None,
    )
    dispatch = await stripe_event_repo.ensure_dispatch(event_id=record.id, handler="billing_sync")

    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    await stripe_event_repo.mark_dispatch_failed(dispatch.id, error="boom", next_retry_at=future)
    pending = await stripe_event_repo.list_dispatches_for_retry(limit=10, ready_before=datetime.now(timezone.utc))
    assert pending == []

    await stripe_event_repo.mark_dispatch_failed(
        dispatch.id,
        error="boom",
        next_retry_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    ready = await stripe_event_repo.list_dispatches_for_retry(limit=10, ready_before=datetime.now(timezone.utc))
    assert len(ready) == 1
    assert ready[0].id == dispatch.id
