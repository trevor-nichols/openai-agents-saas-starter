"""Integration tests for the billing stream SSE endpoint."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies.auth import require_current_user
from app.api.v1.billing.router import router as billing_router
from app.core.config import get_settings
from app.services.billing_events import BillingEventsService, billing_events_service
from app.services.stripe_event_models import (
    DispatchBroadcastContext,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)
from tests.utils.fake_billing_backend import QueueBillingEventBackend

pytestmark = pytest.mark.stripe_replay


@pytest.fixture(autouse=True)
def enable_stream(monkeypatch):
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sse_emits_events(monkeypatch):
    service = BillingEventsService()
    backend = QueueBillingEventBackend()
    service.configure(backend=backend, repository=None)

    monkeypatch.setattr("app.services.billing_events._billing_events_service", service, raising=False)
    monkeypatch.setattr("app.services.billing_events.billing_events_service", service, raising=False)

    app = FastAPI()
    app.dependency_overrides[require_current_user] = lambda: {"sub": "tester"}
    app.include_router(billing_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream(
            "GET",
            "/api/v1/billing/stream",
            headers={"X-Tenant-Id": "tenant-123", "X-Tenant-Role": "owner"},
        ) as response:
            assert response.status_code == 200

            await _publish_invoice_event(service)

            collected = ""
            async for chunk in response.aiter_text():
                collected += chunk
                if "data:" in collected:
                    break
            payload = _extract_event_payload(collected)
            assert payload["event_type"] == "invoice.payment_succeeded"
            assert payload["subscription"]["plan_code"] == "starter"
            assert payload["invoice"]["status"] == "paid"
            assert payload["usage"][0]["feature_key"] == "messages"


async def _publish_invoice_event(service: BillingEventsService) -> None:
    now = datetime.now(timezone.utc)
    record = SimpleNamespace(
        tenant_hint="tenant-123",
        event_type="invoice.payment_succeeded",
        stripe_event_id="evt_stream",
        processed_at=now,
        received_at=now,
        payload={"data": {"object": {"status": "paid"}}},
    )
    context = DispatchBroadcastContext(
        tenant_id="tenant-123",
        event_type="invoice.payment_succeeded",
        summary="Invoice paid",
        status="paid",
        subscription=SubscriptionSnapshotView(
            tenant_id="tenant-123",
            plan_code="starter",
            status="active",
            auto_renew=True,
            seat_count=5,
            current_period_start=now,
            current_period_end=now,
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=InvoiceSnapshotView(
            tenant_id="tenant-123",
            invoice_id="in_test",
            status="paid",
            amount_due_cents=1200,
            currency="usd",
            billing_reason="subscription_cycle",
            hosted_invoice_url="https://example.com",
            collection_method="charge_automatically",
            period_start=now,
            period_end=now,
        ),
        usage=[
            UsageDelta(
                feature_key="messages",
                quantity=42,
                period_start=now,
                period_end=now,
                idempotency_key="line-1",
                amount_cents=300,
            )
        ],
    )
    await service.publish_from_event(record, record.payload, context=context)


def _extract_event_payload(stream_buffer: str) -> dict:
    for block in stream_buffer.split("\n\n"):
        if block.startswith("data:"):
            raw = block.replace("data:", "", 1).strip()
            return json.loads(raw)
    raise AssertionError("No SSE data payload found")
