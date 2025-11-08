"""Unit tests for billing events service."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from fakeredis.aioredis import FakeRedis

from types import SimpleNamespace

from app.services.billing_events import BillingEventsService, RedisBillingEventBackend
from app.services.stripe_event_models import (
    DispatchBroadcastContext,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)


class FlakyBackend(RedisBillingEventBackend):
    def __init__(self, fail_count: int) -> None:
        super().__init__(FakeRedis())
        self.fail_count = fail_count

    async def publish(self, channel: str, message: str) -> None:
        if self.fail_count > 0:
            self.fail_count -= 1
            raise RuntimeError("backend unavailable")
        await super().publish(channel, message)


@pytest.mark.asyncio
async def test_publish_from_event_queues_payload():
    backend = RedisBillingEventBackend(FakeRedis())
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)

    event = _make_event()

    await service.publish_from_event(event, event.payload)

    stream = await service.subscribe("tenant-1")
    message = await stream.next_message(timeout=0.1)
    await stream.close()
    assert message is not None
    data = json.loads(message)
    assert data["event_type"] == "invoice.payment_failed"
    assert data["usage"] == []


@pytest.mark.asyncio
async def test_publish_includes_dispatch_context():
    backend = RedisBillingEventBackend(FakeRedis())
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)

    event = _make_event()
    context = DispatchBroadcastContext(
        tenant_id=event.tenant_hint,
        event_type=event.event_type,
        summary="Invoice paid",
        status="paid",
        subscription=SubscriptionSnapshotView(
            tenant_id=event.tenant_hint,
            plan_code="starter",
            status="active",
            auto_renew=True,
            seat_count=1,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=InvoiceSnapshotView(
            tenant_id=event.tenant_hint,
            invoice_id="in_test",
            status="paid",
            amount_due_cents=1000,
            currency="usd",
            billing_reason="subscription_cycle",
            hosted_invoice_url="https://example.com",
            collection_method="charge_automatically",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
        ),
        usage=[
            UsageDelta(
                feature_key="messages",
                quantity=10,
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                amount_cents=500,
            )
        ],
    )

    await service.publish_from_event(event, event.payload, context=context)

    stream = await service.subscribe("tenant-1")
    message = await stream.next_message(timeout=0.1)
    await stream.close()
    assert message is not None
    payload = json.loads(message)
    assert payload["subscription"]["plan_code"] == "starter"
    assert payload["invoice"]["status"] == "paid"
    assert payload["usage"][0]["feature_key"] == "messages"


@pytest.mark.asyncio
async def test_publish_retries_on_backend_failure(monkeypatch):
    backend = FlakyBackend(fail_count=1)
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)
    service._publish_retry_attempts = 2
    service._publish_retry_delay_seconds = 0

    async def no_sleep(*_):
        return None

    monkeypatch.setattr("app.services.billing_events.asyncio.sleep", no_sleep)

    await service.publish_from_event(_make_event(), {"data": {"object": {"metadata": {"tenant_id": "tenant-1"}}}})


@pytest.mark.asyncio
async def test_publish_raises_after_max_attempts(monkeypatch):
    backend = FlakyBackend(fail_count=5)
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)
    service._publish_retry_attempts = 2
    service._publish_retry_delay_seconds = 0

    async def no_sleep(*_):
        return None

    monkeypatch.setattr("app.services.billing_events.asyncio.sleep", no_sleep)

    with pytest.raises(RuntimeError):
        await service.publish_from_event(_make_event(), {"data": {"object": {"metadata": {"tenant_id": "tenant-1"}}}})


def _make_event(tenant: str = "tenant-1") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        stripe_event_id="evt_unit",
        event_type="invoice.payment_failed",
        payload={"data": {"object": {"metadata": {"tenant_id": tenant}, "status": "failed"}}},
        tenant_hint=tenant,
        processed_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        processing_outcome="processed",
    )
