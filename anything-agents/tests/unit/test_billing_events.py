"""Unit tests for billing events service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.services.billing_events import BillingEventsService, InMemoryBillingEventBackend
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_publish_from_event_queues_payload():
    backend = InMemoryBillingEventBackend()
    service = BillingEventsService()
    service.configure(backend=backend, repository=None)

    event = SimpleNamespace(
        id=uuid.uuid4(),
        stripe_event_id="evt_unit",
        event_type="invoice.payment_failed",
        payload={"data": {"object": {"metadata": {"tenant_id": "tenant-1"}, "status": "failed"}}},
        tenant_hint="tenant-1",
        processed_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        processing_outcome="processed",
    )

    await service.publish_from_event(event, event.payload)

    stream = await service.subscribe("tenant-1")
    message = await stream.next_message(timeout=0.1)
    await stream.close()
    assert message is not None
    assert "invoice.payment_failed" in message
