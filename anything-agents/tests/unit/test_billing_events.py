"""Unit tests for billing events service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from types import SimpleNamespace

from app.services.billing_events import BillingEventsService, InMemoryBillingEventBackend


class FlakyBackend(InMemoryBillingEventBackend):
    def __init__(self, fail_count: int) -> None:
        super().__init__()
        self.fail_count = fail_count

    async def publish(self, channel: str, message: str) -> None:
        if self.fail_count > 0:
            self.fail_count -= 1
            raise RuntimeError("backend unavailable")
        await super().publish(channel, message)


@pytest.mark.asyncio
async def test_publish_from_event_queues_payload():
    backend = InMemoryBillingEventBackend()
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)

    event = _make_event()

    await service.publish_from_event(event, event.payload)

    stream = await service.subscribe("tenant-1")
    message = await stream.next_message(timeout=0.1)
    await stream.close()
    assert message is not None
    assert "invoice.payment_failed" in message


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
