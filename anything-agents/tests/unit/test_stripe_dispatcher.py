"""Unit tests for the Stripe event dispatcher."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
)
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.billing_service import ProcessorInvoiceSnapshot, ProcessorSubscriptionSnapshot
from app.services.stripe_dispatcher import EventHandler, StripeEventDispatcher

FIXTURES = Path("anything-agents/tests/fixtures/stripe")


class FakeBillingService:
    def __init__(self) -> None:
        self.subscription_snapshots: list[ProcessorSubscriptionSnapshot] = []
        self.invoice_snapshots: list[ProcessorInvoiceSnapshot] = []

    async def sync_subscription_from_processor(
        self,
        snapshot: ProcessorSubscriptionSnapshot,
        *,
        processor_name: str = "stripe",
    ) -> None:
        self.subscription_snapshots.append(snapshot)

    async def ingest_invoice_snapshot(self, snapshot: ProcessorInvoiceSnapshot) -> None:
        self.invoice_snapshots.append(snapshot)


@pytest.fixture
async def dispatcher_repo() -> StripeEventRepository:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(StripeEvent.__table__.create)
        await conn.run_sync(StripeEventDispatch.__table__.create)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repo = StripeEventRepository(session_factory)
    try:
        yield repo
    finally:
        await engine.dispose()


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_dispatcher_processes_subscription_event(dispatcher_repo: StripeEventRepository):
    payload = _load_fixture("customer.subscription.created.json")
    payload["data"]["object"].setdefault("metadata", {})["plan_code"] = "starter"
    event, _ = await dispatcher_repo.upsert_event(
        stripe_event_id=payload["id"],
        event_type=payload["type"],
        payload=payload,
        tenant_hint="11111111-2222-3333-4444-555555555555",
        stripe_created_at=None,
    )
    fake_billing = FakeBillingService()
    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=dispatcher_repo, billing=fake_billing)  # type: ignore[arg-type]

    result = await dispatcher.dispatch_now(event, payload)

    assert result.processed_at is not None
    assert fake_billing.subscription_snapshots
    snapshot = fake_billing.subscription_snapshots[0]
    assert snapshot.tenant_id == "11111111-2222-3333-4444-555555555555"
    assert result.broadcast is not None
    assert result.broadcast.subscription is not None
    assert result.broadcast.subscription.plan_code == "starter"


@pytest.mark.asyncio
async def test_dispatcher_raises_for_missing_metadata(dispatcher_repo: StripeEventRepository):
    payload = _load_fixture("customer.subscription.created.json")
    payload["data"]["object"].pop("metadata", None)
    event, _ = await dispatcher_repo.upsert_event(
        stripe_event_id="evt_missing",
        event_type=payload["type"],
        payload=payload,
        tenant_hint=None,
        stripe_created_at=None,
    )
    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=dispatcher_repo, billing=FakeBillingService())  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await dispatcher.dispatch_now(event, payload)


@pytest.mark.asyncio
async def test_dispatcher_processes_invoice_event(dispatcher_repo: StripeEventRepository):
    payload = _load_fixture("invoice.payment_succeeded.json")
    event, _ = await dispatcher_repo.upsert_event(
        stripe_event_id=payload["id"],
        event_type=payload["type"],
        payload=payload,
        tenant_hint="11111111-2222-3333-4444-555555555555",
        stripe_created_at=None,
    )
    fake_billing = FakeBillingService()
    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=dispatcher_repo, billing=fake_billing)  # type: ignore[arg-type]

    result = await dispatcher.dispatch_now(event, payload)

    assert result.processed_at is not None
    assert fake_billing.invoice_snapshots
    context = result.broadcast
    assert context is not None
    assert context.invoice is not None
    assert context.invoice.invoice_id == "in_paid"
    assert context.usage


@pytest.mark.asyncio
async def test_invoice_event_without_metadata(dispatcher_repo: StripeEventRepository):
    payload = _load_fixture("invoice.payment_succeeded.json")
    payload["data"]["object"].pop("metadata", None)
    event, _ = await dispatcher_repo.upsert_event(
        stripe_event_id="evt_invoice_missing",
        event_type=payload["type"],
        payload=payload,
        tenant_hint=None,
        stripe_created_at=None,
    )
    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=dispatcher_repo, billing=FakeBillingService())  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await dispatcher.dispatch_now(event, payload)


@pytest.mark.asyncio
async def test_dispatcher_schedules_retry_on_failure(dispatcher_repo: StripeEventRepository):
    payload = _load_fixture("customer.subscription.created.json")
    payload["data"]["object"].setdefault("metadata", {})["plan_code"] = "starter"
    event, _ = await dispatcher_repo.upsert_event(
        stripe_event_id="evt_retry_handler",
        event_type=payload["type"],
        payload=payload,
        tenant_hint="tenant-retry",
        stripe_created_at=None,
    )
    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=dispatcher_repo, billing=FakeBillingService())  # type: ignore[arg-type]

    async def failing_handler(*_):
        raise RuntimeError("boom")

    dispatcher._handlers[event.event_type] = EventHandler("billing_sync", failing_handler)  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError):
        await dispatcher.dispatch_now(event, payload)

    failed = await dispatcher_repo.list_dispatches(
        handler="billing_sync",
        status=StripeDispatchStatus.FAILED.value,
        limit=1,
    )
    assert failed
    dispatch_row, _ = failed[0]
    assert dispatch_row.next_retry_at is not None
