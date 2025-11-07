"""Integration tests for the Stripe webhook endpoint."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import stripe
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.persistence.stripe.models import StripeEvent
from app.infrastructure.persistence.stripe.repository import (
    StripeEventRepository,
    StripeEventStatus,
    configure_stripe_event_repository,
    reset_stripe_event_repository,
)
from app.presentation.webhooks import stripe as stripe_webhook
from app.services.billing_events import BillingEventsService, InMemoryBillingEventBackend, billing_events_service

import app.infrastructure.persistence.conversations.models  # noqa: F401
import app.infrastructure.persistence.auth.models  # noqa: F401

pytestmark = pytest.mark.stripe_replay


@pytest.fixture(autouse=True)
def configure_secret(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.fixture
async def sqlite_stripe_repo():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(StripeEvent.__table__.create)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repo = StripeEventRepository(session_factory)
    configure_stripe_event_repository(repo)
    try:
        yield repo
    finally:
        reset_stripe_event_repository()
        await engine.dispose()


@pytest.fixture
def webhook_app():
    app = FastAPI()
    app.include_router(stripe_webhook.router)
    return app


@pytest.fixture
def in_memory_billing_events(monkeypatch):
    service = BillingEventsService()
    backend = InMemoryBillingEventBackend()
    service.configure(backend=backend, repository=None)
    monkeypatch.setattr("app.services.billing_events._billing_events_service", service, raising=False)
    monkeypatch.setattr("app.services.billing_events.billing_events_service", service, raising=False)
    return service


def _signature(payload: str, secret: str) -> str:
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload}".encode("utf-8")
    import hmac
    import hashlib

    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "stripe"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fixture_name, tenant_id", 
    [
        ("customer.subscription.created.json", "11111111-2222-3333-4444-555555555555"),
        ("invoice.payment_failed.json", "11111111-2222-3333-4444-555555555555"),
    ],
)
async def test_webhook_replays_fixture(
    fixture_name: str,
    tenant_id: str,
    webhook_app: FastAPI,
    sqlite_stripe_repo: StripeEventRepository,
    in_memory_billing_events: BillingEventsService,
):
    body = load_fixture(fixture_name)
    payload = json.loads(body)

    headers = {
        "stripe-signature": _signature(body, "whsec_test"),
        "content-type": "application/json",
    }

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/webhooks/stripe", content=body, headers=headers)

    assert resp.status_code == 202
    stored = await sqlite_stripe_repo.get_by_event_id(payload["id"])
    assert stored is not None
    assert stored.processing_outcome == StripeEventStatus.PROCESSED.value
    assert stored.tenant_hint == tenant_id

    stream = await in_memory_billing_events.subscribe(tenant_id)
    message = await stream.next_message(timeout=0.2)
    await stream.close()
    assert message is not None
    assert payload["type"] in message


@pytest.mark.asyncio
async def test_duplicate_event_is_acknowledged(
    webhook_app: FastAPI,
    sqlite_stripe_repo: StripeEventRepository,
    in_memory_billing_events: BillingEventsService,
):
    body = load_fixture("invoice.payment_failed.json")
    headers = {
        "stripe-signature": _signature(body, "whsec_test"),
        "content-type": "application/json",
    }

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post("/webhooks/stripe", content=body, headers=headers)
        second = await client.post("/webhooks/stripe", content=body, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    payload = json.loads(body)
    stored = await sqlite_stripe_repo.get_by_event_id(payload["id"])
    assert stored is not None
    assert stored.processing_attempts >= 1


@pytest.mark.asyncio
async def test_invalid_signature_returns_400(webhook_app: FastAPI, sqlite_stripe_repo: StripeEventRepository):
    body = json.dumps({"id": "evt_bad", "type": "invoice.payment_failed"})
    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/webhooks/stripe",
            content=body,
            headers={"stripe-signature": "t=0,v1=bad", "content-type": "application/json"},
        )

    assert resp.status_code == 400
    assert await sqlite_stripe_repo.get_by_event_id("evt_bad") is None
