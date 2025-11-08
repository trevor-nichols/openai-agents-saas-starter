"""Contract tests for human authentication endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_token_signer
from app.services.auth_service import (
    UserAuthenticationError,
    UserRefreshError,
    UserSessionTokens,
)
from app.services.user_service import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    UserLockedError,
)
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _make_session_tokens() -> UserSessionTokens:
    now = datetime.now(UTC)
    return UserSessionTokens(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=now + timedelta(minutes=15),
        refresh_expires_at=now + timedelta(days=7),
        kid="kid-primary",
        refresh_kid="kid-refresh",
        scopes=["conversations:read"],
        tenant_id=str(uuid4()),
        user_id=str(uuid4()),
    )


@pytest.fixture
def fake_auth_service(monkeypatch: pytest.MonkeyPatch):
    mock_service = AsyncMock()
    monkeypatch.setattr("app.api.v1.auth.router.auth_service", mock_service)
    return mock_service


def _mint_user_token(*, token_use: str) -> tuple[str, str]:
    signer = get_token_signer()
    now = datetime.now(UTC)
    subject = f"user:{uuid4()}"
    payload = {
        "sub": subject,
        "scope": "conversations:read",
        "token_use": token_use,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    token = signer.sign(payload).primary.token
    return token, subject


def test_login_success_includes_client_context(fake_auth_service, client: TestClient) -> None:
    tokens = _make_session_tokens()
    fake_auth_service.login_user.return_value = tokens

    payload = {
        "email": "owner@example.com",
        "password": "P@ssword12345!",
        "tenant_id": str(uuid4()),
    }
    headers = {"X-Forwarded-For": "203.0.113.10", "User-Agent": "pytest-agent"}

    response = client.post("/api/v1/auth/token", json=payload, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"] == tokens.access_token
    assert body["refresh_token"] == tokens.refresh_token
    assert body["kid"] == tokens.kid
    assert body["user_id"] == tokens.user_id

    fake_auth_service.login_user.assert_awaited_once()
    kwargs = fake_auth_service.login_user.await_args.kwargs
    assert kwargs["email"] == payload["email"]
    assert kwargs["tenant_id"] == payload["tenant_id"]
    assert kwargs["ip_address"] == "203.0.113.10"
    assert kwargs["user_agent"] == "pytest-agent"


def test_login_invalid_credentials_returns_401(fake_auth_service, client: TestClient) -> None:
    async def _raise_invalid(**_: object) -> None:
        raise UserAuthenticationError("Invalid email or password.") from InvalidCredentialsError(
            "Invalid email or password."
        )

    fake_auth_service.login_user.side_effect = _raise_invalid

    response = client.post(
        "/api/v1/auth/token",
        json={"email": "owner@example.com", "password": "wrong-password", "tenant_id": None},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Invalid email or password."
    assert body["error"] == "Invalid email or password."


def test_login_locked_account_returns_423(fake_auth_service, client: TestClient) -> None:
    async def _raise_locked(**_: object) -> None:
        raise UserAuthenticationError("Account locked.") from UserLockedError(
            "Account locked due to failures."
        )

    fake_auth_service.login_user.side_effect = _raise_locked

    response = client.post(
        "/api/v1/auth/token",
        json={"email": "owner@example.com", "password": "whatever", "tenant_id": None},
    )

    assert response.status_code == 423
    body = response.json()
    assert body["message"] == "Account locked due to failures."
    assert body["error"] == "Account locked due to failures."


def test_login_missing_tenant_returns_401(fake_auth_service, client: TestClient) -> None:
    async def _raise_membership(**_: object) -> None:
        raise UserAuthenticationError(
            "User is not assigned to this tenant."
        ) from MembershipNotFoundError("User is not assigned to this tenant.")

    fake_auth_service.login_user.side_effect = _raise_membership

    response = client.post(
        "/api/v1/auth/token",
        json={"email": "owner@example.com", "password": "whatever", "tenant_id": str(uuid4())},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "User is not assigned to this tenant."
    assert body["error"] == "User is not assigned to this tenant."


def test_refresh_success_returns_new_tokens(fake_auth_service, client: TestClient) -> None:
    tokens = _make_session_tokens()
    fake_auth_service.refresh_user_session.return_value = tokens

    headers = {"User-Agent": "pytest-agent"}
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "refresh-token-value"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["refresh_token"] == tokens.refresh_token
    assert body["refresh_kid"] == tokens.refresh_kid
    fake_auth_service.refresh_user_session.assert_awaited_once()
    args = fake_auth_service.refresh_user_session.await_args.args
    kwargs = fake_auth_service.refresh_user_session.await_args.kwargs
    assert args[0] == "refresh-token-value"
    assert kwargs["user_agent"] == "pytest-agent"


def test_refresh_revoked_returns_401(fake_auth_service, client: TestClient) -> None:
    async def _raise_revoked(*_: object, **__: object) -> None:
        raise UserRefreshError("Refresh token has been revoked or expired.")

    fake_auth_service.refresh_user_session.side_effect = _raise_revoked

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "stale-token-value"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Refresh token has been revoked or expired."
    assert body["error"] == "Refresh token has been revoked or expired."


def test_me_endpoint_accepts_access_token(client: TestClient) -> None:
    token, subject = _mint_user_token(token_use="access")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["user_id"] == subject.split("user:", 1)[1]


def test_me_endpoint_rejects_refresh_token(client: TestClient) -> None:
    token, _ = _mint_user_token(token_use="refresh")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "Access token required."
