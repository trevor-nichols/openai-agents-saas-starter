from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.contact.router import router
from app.services.contact_service import ContactSubmissionResult
from app.services.shared.rate_limit_service import RateLimitExceeded, rate_limiter


class StubContactService:
    def __init__(self) -> None:
        self.called_with: dict[str, str | None] | None = None

    async def submit_contact(self, **kwargs) -> ContactSubmissionResult:
        self.called_with = kwargs
        return ContactSubmissionResult(
            reference_id="ref-123",
            delivered=True,
            message_id="msg-1",
        )


@pytest.fixture()
def stub_service(monkeypatch: pytest.MonkeyPatch) -> StubContactService:
    service = StubContactService()
    monkeypatch.setattr("app.api.v1.contact.router.get_contact_service", lambda: service)

    async def _noop_enforce(*args, **kwargs):
        return None

    monkeypatch.setattr(rate_limiter, "enforce", _noop_enforce)
    return service


@pytest.fixture()
def client(stub_service: StubContactService) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_contact_submission_returns_success(client: TestClient, stub_service: StubContactService) -> None:
    payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "company": "Analytical Engines",
        "topic": "Partnership",
        "message": "We would like to collaborate on a deployment.",
    }

    response = client.post("/api/v1/contact", json=payload)

    assert response.status_code == 202
    body = response.json()
    assert body["success"] is True
    assert body["data"]["reference_id"] == "ref-123"
    assert stub_service.called_with is not None
    assert stub_service.called_with["email"] == "ada@example.com"


def test_contact_submission_is_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise(*args, **kwargs):
        raise RateLimitExceeded(quota="contact_ip", limit=1, retry_after=1, scope="ip")

    monkeypatch.setattr(rate_limiter, "enforce", _raise)
    monkeypatch.setattr(
        "app.api.v1.contact.router.get_contact_service",
        lambda: StubContactService(),
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post(
        "/api/v1/contact",
        json={
            "email": "throttle@example.com",
            "message": "Test message exceeding min length.",
        },
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers

