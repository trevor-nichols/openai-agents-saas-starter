"""Unit tests for the test fixture seeding API router."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.test_fixtures.router import router as test_fixture_router
from app.core.config import get_settings
from app.services.signup.email_verification_service import EmailVerificationTokenIssueResult
from app.services.test_fixtures import FixtureApplyResult


def _create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(test_fixture_router, prefix="/api/v1")
    return app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.delenv("USE_TEST_FIXTURES", raising=False)
    get_settings.cache_clear()
    application = _create_app()
    with TestClient(application) as client:
        yield client


def test_apply_fixtures_returns_404_when_disabled(app: TestClient) -> None:
    response = app.post(
        "/api/v1/test-fixtures/apply",
        json={"tenants": [{"slug": "alpha", "name": "Alpha"}]},
    )
    assert response.status_code == 404


def test_apply_fixtures_invokes_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_TEST_FIXTURES", "true")
    get_settings.cache_clear()
    application = _create_app()

    fake_result = FixtureApplyResult.model_validate(
        {
            "tenants": {
                "alpha": {
                    "tenant_id": "00000000-0000-0000-0000-000000000001",
                    "plan_code": "starter",
                    "users": {
                        "admin@example.com": {
                            "user_id": "00000000-0000-0000-0000-000000000002",
                            "role": "owner",
                        }
                    },
                    "conversations": {
                        "intro": {
                            "conversation_id": "00000000-0000-0000-0000-000000000003",
                            "status": "active",
                        }
                    },
                }
            },
            "generated_at": "2025-01-01T00:00:00Z",
        }
    )

    async def _fake_apply(_self, spec):
        return fake_result

    monkeypatch.setattr(
        "app.api.v1.test_fixtures.router.TestFixtureService.apply_spec",
        _fake_apply,
    )

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/test-fixtures/apply",
            json={"tenants": [{"slug": "alpha", "name": "Alpha"}]},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["tenants"]["alpha"]["plan_code"] == "starter"


def test_issue_email_token_requires_fixture_flag(app: TestClient) -> None:
    response = app.post(
        "/api/v1/test-fixtures/email-verification-token",
        json={"email": "owner@example.com"},
    )
    assert response.status_code == 404


def test_issue_email_token_returns_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_TEST_FIXTURES", "true")
    get_settings.cache_clear()
    application = _create_app()

    issued = EmailVerificationTokenIssueResult(
        token="abcd.efgh",
        user_id=UUID("00000000-0000-0000-0000-0000000000aa"),
        expires_at=datetime.fromisoformat("2025-01-01T00:05:00+00:00"),
    )

    class _FakeService:
        async def issue_token_for_testing(self, **kwargs):
            _ = kwargs
            return issued

    monkeypatch.setattr(
        "app.api.v1.test_fixtures.router.get_email_verification_service",
        lambda: _FakeService(),
    )

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/test-fixtures/email-verification-token",
            json={"email": "owner@example.com"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["token"] == "abcd.efgh"
    assert payload["user_id"] == str(issued.user_id)
