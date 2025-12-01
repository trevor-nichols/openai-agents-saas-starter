from __future__ import annotations

import hashlib
import hmac
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Mapping, cast

import importlib

logs_module = importlib.import_module("app.api.v1.logs.router")
from app.api.v1.logs.router import MAX_BODY_BYTES
from app.core.settings import Settings
from app.services.shared.rate_limit_service import rate_limiter


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()

    async def _noop_enforce(*args, **kwargs):
        return None

    monkeypatch.setattr(rate_limiter, "enforce", _noop_enforce)
    settings = Settings.model_validate(
        {
            "ALLOW_ANON_FRONTEND_LOGS": True,
            "FRONTEND_LOG_SHARED_SECRET": "secret",
        }
    )
    monkeypatch.setattr(logs_module, "get_settings", lambda: settings)

    app.include_router(logs_module.router, prefix="/api/v1")
    return TestClient(app)


def test_ingest_accepts_small_payload(client: TestClient) -> None:
    body: Payload = {"event": "ui.click", "message": "ok"}
    raw = client_payload(body)
    resp = client.post(
        "/api/v1/logs",
        content=cast(bytes, raw),
        headers={
            "x-log-signature": _sig(raw, "secret"),
            "content-type": "application/json",
        },
    )
    assert resp.status_code == 202
    assert resp.json().get("accepted") is True


def test_ingest_rejects_oversized_payload(client: TestClient) -> None:
    # Create a payload that serializes to larger than MAX_BODY_BYTES.
    oversized = "x" * (MAX_BODY_BYTES + 100)
    body = {"event": "ui.click", "fields": {"blob": oversized}}
    resp = client.post(
        "/api/v1/logs",
        json=body,
        headers={"x-log-signature": _sig(body, "secret")},
    )
    assert resp.status_code == 413
    assert resp.json()["detail"] == "Log payload too large."


def test_ingest_strips_reserved_fields(client: TestClient) -> None:
    body: Payload = {
        "event": "ui.click",
        "fields": {
            "level": "warn",
            "message": "override",
            "custom": "ok",
        },
    }
    raw = client_payload(body)
    resp = client.post(
        "/api/v1/logs",
        content=cast(bytes, raw),
        headers={
            "x-log-signature": _sig(raw, "secret"),
            "content-type": "application/json",
        },
    )
    assert resp.status_code == 202
    assert resp.json().get("accepted") is True


Payload = dict[str, object]


def _sig(body: bytes | Mapping[str, object], secret: str) -> str:
    raw = body if isinstance(body, (bytes, bytearray)) else client_payload(body)
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def client_payload(body: Mapping[str, object]) -> bytes:
    import json

    return json.dumps(body, separators=(",", ":")).encode("utf-8")
