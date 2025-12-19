from __future__ import annotations

import importlib
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_exception_handlers
from app.core.settings import Settings

stripe_module = importlib.import_module("app.presentation.webhooks.stripe")


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    settings = Settings.model_validate(
        {
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }
    )
    monkeypatch.setattr(stripe_module, "get_settings", lambda: settings)
    app.include_router(stripe_module.router)
    return TestClient(app)


def test_webhook_rejects_missing_signature(client: TestClient) -> None:
    resp = client.post("/webhooks/stripe", content=b"{}", headers={"content-type": "application/json"})
    assert resp.status_code == 400
    payload: dict[str, Any] = resp.json()
    assert payload["success"] is False
    assert payload["error"] == "MissingStripeSignature"
    assert payload["message"] == "Missing Stripe signature header."


def test_webhook_rejects_invalid_payload(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    # Ensure repository is not reached for invalid payload.
    monkeypatch.setattr(stripe_module, "get_stripe_event_repository", lambda: (_ for _ in ()).throw(AssertionError()))

    def _raise_value_error(*args, **kwargs):
        raise ValueError("bad json")

    monkeypatch.setattr(stripe_module.stripe.Webhook, "construct_event", _raise_value_error)

    resp = client.post(
        "/webhooks/stripe",
        content=b"not-json",
        headers={"content-type": "application/json", "stripe-signature": "sig"},
    )
    assert resp.status_code == 400
    payload: dict[str, Any] = resp.json()
    assert payload["error"] == "InvalidStripePayload"
    assert payload["message"] == "Invalid payload."


def test_webhook_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    class _SigError(Exception):
        pass

    monkeypatch.setattr(stripe_module, "SignatureVerificationError", _SigError)

    def _raise_sig_error(*args, **kwargs):
        raise _SigError("bad sig")

    monkeypatch.setattr(stripe_module.stripe.Webhook, "construct_event", _raise_sig_error)

    resp = client.post(
        "/webhooks/stripe",
        content=b"{}",
        headers={"content-type": "application/json", "stripe-signature": "sig"},
    )
    assert resp.status_code == 400
    payload: dict[str, Any] = resp.json()
    assert payload["error"] == "InvalidStripeSignature"
    assert payload["message"] == "Signature verification failed."

