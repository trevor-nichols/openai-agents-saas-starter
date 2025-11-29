from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_current_user
from app.api.v1.logs.router import MAX_BODY_BYTES, router
from app.services.shared.rate_limit_service import rate_limiter


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()

    async def _fake_user():
        return {"tenant_id": "t1", "sub": "u1"}

    app.dependency_overrides[require_current_user] = _fake_user

    async def _noop_enforce(*args, **kwargs):
        return None

    monkeypatch.setattr(rate_limiter, "enforce", _noop_enforce)

    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_ingest_accepts_small_payload(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/logs",
        json={"event": "ui.click", "message": "ok"},
    )
    assert resp.status_code == 202
    assert resp.json().get("accepted") is True


def test_ingest_rejects_oversized_payload(client: TestClient) -> None:
    # Create a payload that serializes to larger than MAX_BODY_BYTES.
    oversized = "x" * (MAX_BODY_BYTES + 100)
    resp = client.post(
        "/api/v1/logs",
        json={"event": "ui.click", "fields": {"blob": oversized}},
    )
    assert resp.status_code == 413
    assert resp.json()["detail"] == "Log payload too large."


def test_ingest_strips_reserved_fields(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/logs",
        json={
            "event": "ui.click",
            "fields": {
                "level": "warn",
                "message": "override",
                "custom": "ok",
            },
        },
    )
    assert resp.status_code == 202
    assert resp.json().get("accepted") is True
