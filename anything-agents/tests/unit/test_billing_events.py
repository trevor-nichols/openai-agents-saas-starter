"""Unit tests for billing events service."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from fakeredis.aioredis import FakeRedis

from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventStatus
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.observability.metrics import (
    STRIPE_BILLING_STREAM_BACKLOG_SECONDS,
    STRIPE_BILLING_STREAM_EVENTS_TOTAL,
)
from app.services.billing.billing_events import BillingEventsService, RedisBillingEventBackend
from app.services.billing.stripe.event_models import (
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
    tenant_id = _tenant_hint(event)
    context = DispatchBroadcastContext(
        tenant_id=tenant_id,
        event_type=event.event_type,
        summary="Invoice paid",
        status="paid",
        subscription=SubscriptionSnapshotView(
            tenant_id=tenant_id,
            plan_code="starter",
            status="active",
            auto_renew=True,
            seat_count=1,
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC),
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=InvoiceSnapshotView(
            tenant_id=tenant_id,
            invoice_id="in_test",
            status="paid",
            amount_due_cents=1000,
            currency="usd",
            billing_reason="subscription_cycle",
            hosted_invoice_url="https://example.com",
            collection_method="charge_automatically",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
        ),
        usage=[
            UsageDelta(
                feature_key="messages",
                quantity=10,
                period_start=datetime.now(UTC),
                period_end=datetime.now(UTC),
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

    monkeypatch.setattr("app.services.billing.billing_events.asyncio.sleep", no_sleep)

    await service.publish_from_event(
        _make_event(), {"data": {"object": {"metadata": {"tenant_id": "tenant-1"}}}}
    )


@pytest.mark.asyncio
async def test_publish_raises_after_max_attempts(monkeypatch):
    backend = FlakyBackend(fail_count=5)
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)
    service._publish_retry_attempts = 2
    service._publish_retry_delay_seconds = 0

    async def no_sleep(*_):
        return None

    monkeypatch.setattr("app.services.billing.billing_events.asyncio.sleep", no_sleep)

    with pytest.raises(RuntimeError):
        await service.publish_from_event(
            _make_event(), {"data": {"object": {"metadata": {"tenant_id": "tenant-1"}}}}
        )


def _make_event(
    tenant: str = "tenant-1",
    *,
    stripe_event_id: str | None = None,
    event_type: str = "invoice.payment_failed",
    received_at: datetime | None = None,
    payload: dict[str, Any] | None = None,
) -> StripeEvent:
    now = received_at or datetime.now(UTC)
    body: dict[str, Any]
    if payload is None:
        body = {
            "data": {"object": {"metadata": {"tenant_id": tenant}, "status": "failed"}}
        }
    else:
        body = payload
    if "data" not in body:
        body = cast(dict[str, Any], {"data": {"object": body}})
    return StripeEvent(
        id=uuid.uuid4(),
        stripe_event_id=stripe_event_id or f"evt_{uuid.uuid4().hex[:8]}",
        event_type=event_type,
        payload=body,
        tenant_hint=tenant,
        processed_at=now,
        received_at=now,
        processing_outcome=StripeEventStatus.PROCESSED.value,
    )


def _tenant_hint(event: StripeEvent) -> str:
    return cast(str, event.tenant_hint)


@pytest.mark.asyncio
async def test_publish_updates_stream_metrics():
    backend = RedisBillingEventBackend(FakeRedis())
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)

    baseline = _counter_value(
        STRIPE_BILLING_STREAM_EVENTS_TOTAL, source="webhook", result="published"
    )
    event = _make_event()
    tenant_id = _tenant_hint(event)
    context = DispatchBroadcastContext(
        tenant_id=tenant_id,
        event_type=event.event_type,
        summary="Invoice processed",
        status="paid",
        subscription=SubscriptionSnapshotView(
            tenant_id=tenant_id,
            plan_code="starter",
            status="active",
            auto_renew=True,
            seat_count=1,
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC),
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=None,
        usage=[],
    )

    await service.publish_from_event(event, event.payload, context=context)
    await service.mark_processed(event.processed_at)

    updated = _counter_value(
        STRIPE_BILLING_STREAM_EVENTS_TOTAL, source="webhook", result="published"
    )
    assert updated == baseline + 1
    assert STRIPE_BILLING_STREAM_BACKLOG_SECONDS._value.get() >= 0


def _counter_value(metric, **labels) -> float:
    return metric.labels(**labels)._value.get()


class StubStripeEventRepository:
    def __init__(self, events: list[StripeEvent]):
        self._events = events
        self.calls: list[dict[str, Any]] = []

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
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "limit": limit,
                "cursor_received_at": cursor_received_at,
                "cursor_event_id": cursor_event_id,
                "event_type": event_type,
                "status": status,
            }
        )
        return self._events[: limit if limit > 0 else 1]


@pytest.mark.asyncio
async def test_list_history_returns_payloads_and_cursor():
    backend = RedisBillingEventBackend(FakeRedis())
    events = [
        _make_event(
            stripe_event_id="evt-latest",
            received_at=datetime(2024, 1, 2, tzinfo=UTC),
            event_type="invoice.payment_succeeded",
        ),
        _make_event(
            stripe_event_id="evt-older",
            received_at=datetime(2024, 1, 1, tzinfo=UTC),
            event_type="invoice.payment_succeeded",
        ),
    ]
    repository = StubStripeEventRepository(events)
    service = BillingEventsService()
    service.configure(backend=backend, repository=cast(StripeEventRepository, repository))

    page = await service.list_history(tenant_id="tenant-1", limit=1)

    assert page.items and page.items[0].stripe_event_id == "evt-latest"
    assert page.next_cursor is not None
    assert repository.calls and repository.calls[0]["tenant_id"] == "tenant-1"


@pytest.mark.asyncio
async def test_list_history_rejects_invalid_cursor():
    backend = RedisBillingEventBackend(FakeRedis())
    repository = StubStripeEventRepository([])
    service = BillingEventsService()
    service.configure(backend=backend, repository=cast(StripeEventRepository, repository))

    with pytest.raises(ValueError):
        await service.list_history(tenant_id="tenant-1", limit=10, cursor="not-a-cursor")


@pytest.mark.asyncio
async def test_list_history_populates_invoice_fields_from_payload():
    backend = RedisBillingEventBackend(FakeRedis())
    invoice_payload = {
        "data": {
            "object": {
                "id": "in_hist",
                "status": "paid",
                "amount_due": 1200,
                "currency": "usd",
                "billing_reason": "subscription_cycle",
                "hosted_invoice_url": "https://stripe.test/in_hist",
                "collection_method": "charge_automatically",
                "period_start": int(datetime(2024, 1, 1, tzinfo=UTC).timestamp()),
                "period_end": int(datetime(2024, 1, 31, tzinfo=UTC).timestamp()),
                "lines": {
                    "data": [
                        {
                            "id": "line_usage",
                            "quantity": 42,
                            "amount": 300,
                            "period": {
                                "start": int(datetime(2024, 1, 1, tzinfo=UTC).timestamp()),
                                "end": int(datetime(2024, 1, 31, tzinfo=UTC).timestamp()),
                            },
                            "price": {
                                "recurring": {"usage_type": "metered"},
                                "metadata": {"feature_key": "messages"},
                            },
                            "metadata": {},
                        }
                    ]
                },
            }
        }
    }
    event = _make_event(
        stripe_event_id="evt_invoice",
        event_type="invoice.payment_succeeded",
        payload=invoice_payload,
    )
    repository = StubStripeEventRepository([event])
    service = BillingEventsService()
    service.configure(backend=backend, repository=cast(StripeEventRepository, repository))

    page = await service.list_history(tenant_id="tenant-1", limit=1)

    assert page.items and page.items[0].invoice is not None
    assert page.items[0].invoice.invoice_id == "in_hist"
    assert page.items[0].usage and page.items[0].usage[0].feature_key == "messages"


@pytest.mark.asyncio
async def test_list_history_populates_subscription_fields_from_payload():
    backend = RedisBillingEventBackend(FakeRedis())
    subscription_payload = {
        "data": {
            "object": {
                "status": "active",
                "cancel_at_period_end": False,
                "current_period_start": int(datetime(2024, 2, 1, tzinfo=UTC).timestamp()),
                "current_period_end": int(datetime(2024, 2, 29, tzinfo=UTC).timestamp()),
                "trial_end": int(datetime(2024, 2, 5, tzinfo=UTC).timestamp()),
                "cancel_at": None,
                "items": {
                    "data": [
                        {
                            "price": {
                                "metadata": {"plan_code": "pro"},
                                "nickname": "Pro",
                            },
                            "quantity": 5,
                        }
                    ]
                },
            }
        }
    }
    event = _make_event(
        stripe_event_id="evt_sub",
        event_type="customer.subscription.updated",
        payload=subscription_payload,
    )
    repository = StubStripeEventRepository([event])
    service = BillingEventsService()
    service.configure(backend=backend, repository=cast(StripeEventRepository, repository))

    page = await service.list_history(tenant_id="tenant-1", limit=1)

    assert page.items and page.items[0].subscription is not None
    assert page.items[0].subscription.plan_code == "pro"
    assert page.items[0].subscription.seat_count == 5
