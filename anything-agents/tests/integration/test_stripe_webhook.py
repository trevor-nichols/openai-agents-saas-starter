"""Integration tests for the Stripe webhook endpoint."""

from __future__ import annotations

import json
import time

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

import app.infrastructure.persistence.conversations.models  # noqa: F401
import app.infrastructure.persistence.auth.models  # noqa: F401


@pytest.fixture(autouse=True)
def configure_secret(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
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


def _signature(payload: str, secret: str) -> str:
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload}".encode("utf-8")
    import hmac
    import hashlib

    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


@pytest.mark.asyncio
async def test_webhook_persists_event(webhook_app: FastAPI, sqlite_stripe_repo: StripeEventRepository):
    body = json.dumps(
        {
            "id": "evt_webhook",
            "type": "customer.subscription.created",
            "created": int(time.time()),
            "data": {"object": {"metadata": {"tenant_id": "tenant-xyz"}}},
        }
    )

    headers = {
        "stripe-signature": _signature(body, "whsec_test"),
        "content-type": "application/json",
    }

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/webhooks/stripe", content=body, headers=headers)

    assert resp.status_code == 202
    stored = await sqlite_stripe_repo.get_by_event_id("evt_webhook")
    assert stored is not None
    assert stored.processing_outcome == StripeEventStatus.PROCESSED.value
    assert stored.tenant_hint == "tenant-xyz"


@pytest.mark.asyncio
async def test_duplicate_event_is_acknowledged(webhook_app: FastAPI, sqlite_stripe_repo: StripeEventRepository):
    payload = {
        "id": "evt_duplicate",
        "type": "invoice.paid",
        "created": int(time.time()),
        "data": {"object": {"metadata": {}}},
    }
    body = json.dumps(payload)
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
    stored = await sqlite_stripe_repo.get_by_event_id("evt_duplicate")
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
