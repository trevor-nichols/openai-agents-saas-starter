from __future__ import annotations

from uuid import uuid4
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import routes_sessions
from app.services.auth.errors import MfaRequiredError


@pytest.fixture(autouse=True)
async def _configure_agent_provider() -> AsyncGenerator[None, None]:
    # Override the suite-level autouse fixture that bootstraps the OpenAI provider;
    # not needed for these lightweight route tests.
    yield


class _StubAuthService:
    async def login_user(
        self,
        *,
        email: str,
        password: str,
        tenant_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ):
        raise MfaRequiredError(
            "challenge-token",
            [
                {
                    "id": str(uuid4()),
                    "method_type": "totp",
                    "label": "Phone",
                    "verified_at": None,
                    "last_used_at": None,
                    "revoked_at": None,
                }
            ],
        )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    monkeypatch.setattr(routes_sessions, "auth_service", _StubAuthService())
    app.include_router(routes_sessions.router, prefix="/api/v1/auth")
    return TestClient(app)


def test_token_route_returns_mfa_challenge(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/token",
        json={"email": "user@example.com", "password": "longpassword"},
    )

    assert resp.status_code == 202
    body = resp.json()
    assert body["challenge_token"] == "challenge-token"
    assert body["methods"][0]["method_type"] == "totp"
