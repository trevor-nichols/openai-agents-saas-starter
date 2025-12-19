"""Contract tests for human authentication endpoints."""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])

from app.bootstrap import get_container
from app.core.settings import get_settings
from app.core.security import get_token_signer
from app.domain.auth import (
    SessionClientDetails,
    SessionLocation,
    UserSession,
    UserSessionListResult,
)
from app.services.auth_service import (
    UserAuthenticationError,
    UserLogoutError,
    UserRefreshError,
    UserSessionTokens,
)
from app.services.signup.email_verification_service import (
    EmailVerificationDeliveryError,
    InvalidEmailVerificationTokenError,
)
from app.services.signup.password_recovery_service import (
    InvalidPasswordResetTokenError,
    PasswordResetDeliveryError,
)
from app.services.users import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    UserLockedError,
)
from main import app


@pytest.fixture
def client(
    fake_auth_service,
    fake_user_service,
    fake_password_recovery_service,
    fake_email_verification_service,
) -> Generator[TestClient, None, None]:
    """Spin up the FastAPI test client and install mocked services."""

    with TestClient(app) as test_client:
        container = cast(Any, get_container())
        container.auth_service = fake_auth_service
        container.user_service = fake_user_service
        container.password_recovery_service = fake_password_recovery_service
        container.email_verification_service = fake_email_verification_service
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
        email_verified=True,
        session_id=str(uuid4()),
    )


@pytest.fixture
def fake_auth_service():
    mock_service = AsyncMock()
    mock_service.revoke_user_sessions = AsyncMock(return_value=0)
    mock_service.logout_user_session = AsyncMock(return_value=True)
    mock_service.list_user_sessions = AsyncMock()
    mock_service.revoke_user_session_by_id = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def fake_password_recovery_service():
    service = AsyncMock()
    service.request_password_reset = AsyncMock()
    service.confirm_password_reset = AsyncMock()
    return service


@pytest.fixture
def fake_email_verification_service():
    service = AsyncMock()
    service.send_verification_email = AsyncMock(return_value=True)
    service.verify_token = AsyncMock()
    return service


@pytest.fixture
def fake_user_service():
    stub = AsyncMock()
    stub.change_password = AsyncMock()
    stub.admin_reset_password = AsyncMock()
    return stub


def _mint_user_token(
    *,
    token_use: str,
    scope: str = "conversations:read",
    tenant_id: str | None = None,
    email_verified: bool = True,
    session_id: UUID | None = None,
) -> tuple[str, str]:
    signer = get_token_signer()
    now = datetime.now(UTC)
    settings = get_settings()
    subject = f"user:{uuid4()}"
    payload = {
        "sub": subject,
        "scope": scope,
        "token_use": token_use,
        "iss": settings.app_name,
        "aud": settings.auth_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "email_verified": email_verified,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    if session_id:
        payload["sid"] = str(session_id)
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
    assert body["session_id"] == tokens.session_id

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
    assert body["error"] == "Unauthorized"


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
    assert body["error"] == "Locked"


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
    assert body["error"] == "Unauthorized"


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
    assert body["session_id"] == tokens.session_id
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
    assert body["error"] == "Unauthorized"


def test_password_forgot_endpoint(fake_password_recovery_service, client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "owner@example.com"},
        headers={"X-Forwarded-For": "198.51.100.10", "User-Agent": "pytest-agent"},
    )

    assert response.status_code == 202, response.text
    fake_password_recovery_service.request_password_reset.assert_awaited_once()


def test_password_forgot_delivery_failure(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    service = AsyncMock()
    service.request_password_reset = AsyncMock(
        side_effect=PasswordResetDeliveryError("retry later")
    )

    def _get_service() -> AsyncMock:
        return service

    monkeypatch.setattr(
        "app.api.v1.auth.routes_passwords.get_password_recovery_service",
        _get_service,
    )

    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "owner@example.com"},
    )

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == "BadGateway"
    assert body["message"] == "Unable to send password reset email. Please try again shortly."


def test_password_confirm_endpoint_success(
    fake_password_recovery_service, client: TestClient
) -> None:
    response = client.post(
        "/api/v1/auth/password/confirm",
        json={"token": "abc.def", "new_password": "ValidPassword!!12345"},
    )

    assert response.status_code == 200, response.text
    fake_password_recovery_service.confirm_password_reset.assert_awaited_once()


def test_password_confirm_invalid_token_returns_400(
    fake_password_recovery_service, client: TestClient
) -> None:
    async def _raise_invalid(**_: object) -> None:
        raise InvalidPasswordResetTokenError("Password reset token is invalid or expired.")

    fake_password_recovery_service.confirm_password_reset.side_effect = _raise_invalid

    response = client.post(
        "/api/v1/auth/password/confirm",
        json={"token": "bad.token", "new_password": "ValidPassword!!12345"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "BadRequest"
    assert body["message"] == "Password reset token is invalid or expired."


def test_email_send_endpoint(fake_email_verification_service, client: TestClient) -> None:
    token, _ = _mint_user_token(token_use="access", email_verified=False)
    response = client.post(
        "/api/v1/auth/email/send",
        headers={"Authorization": f"Bearer {token}", "X-Forwarded-For": "198.51.100.2"},
    )

    assert response.status_code == 202
    fake_email_verification_service.send_verification_email.assert_awaited_once()


def test_email_send_endpoint_delivery_failure(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    service = AsyncMock()
    service.send_verification_email = AsyncMock(
        side_effect=EmailVerificationDeliveryError("retry later")
    )

    def _get_service() -> AsyncMock:
        return service

    monkeypatch.setattr(
        "app.api.v1.auth.routes_email.get_email_verification_service",
        _get_service,
    )

    token, _ = _mint_user_token(token_use="access", email_verified=False)
    response = client.post(
        "/api/v1/auth/email/send",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == "BadGateway"
    assert body["message"] == "Unable to send verification email. Please try again shortly."


def test_email_send_endpoint_skips_when_verified(client: TestClient) -> None:
    token, _ = _mint_user_token(token_use="access", email_verified=True)
    response = client.post(
        "/api/v1/auth/email/send",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    assert response.json()["data"]["email_verified"] is True


def test_email_verify_endpoint_success(fake_email_verification_service, client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/email/verify",
        json={"token": "abc.def"},
    )

    assert response.status_code == 200
    fake_email_verification_service.verify_token.assert_awaited_once()


def test_email_verify_endpoint_invalid_token(
    fake_email_verification_service, client: TestClient
) -> None:
    async def _raise_invalid(**_: object) -> None:
        raise InvalidEmailVerificationTokenError("Verification token is invalid or expired.")

    fake_email_verification_service.verify_token.side_effect = _raise_invalid

    response = client.post(
        "/api/v1/auth/email/verify",
        json={"token": "bad.token"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "BadRequest"
    assert body["message"] == "Verification token is invalid or expired."


def test_logout_single_session_success(fake_auth_service, client: TestClient) -> None:
    token, subject = _mint_user_token(token_use="access")
    user_id = subject.split("user:", 1)[1]
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "refresh-token"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    fake_auth_service.logout_user_session.assert_awaited_once()
    kwargs = fake_auth_service.logout_user_session.await_args.kwargs
    assert kwargs["refresh_token"] == "refresh-token"
    assert kwargs["expected_user_id"] == user_id


def test_logout_single_session_forbidden_on_service_error(
    fake_auth_service, client: TestClient
) -> None:
    token, _ = _mint_user_token(token_use="access")

    async def _raise_logout(*_: object, **__: object) -> None:
        raise UserLogoutError("Refresh token does not belong to the authenticated user.")

    fake_auth_service.logout_user_session.side_effect = _raise_logout

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "foreign-token"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["message"] == "Refresh token does not belong to the authenticated user."
    assert body["error"] == "Forbidden"


def test_logout_all_endpoint(fake_auth_service, client: TestClient) -> None:
    fake_auth_service.revoke_user_sessions.return_value = 2
    token, _ = _mint_user_token(token_use="access")

    response = client.post(
        "/api/v1/auth/logout/all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    args = fake_auth_service.revoke_user_sessions.await_args
    assert isinstance(args.args[0], UUID)
    assert args.kwargs["reason"] == "user_logout_all"
    body = response.json()
    assert body["data"]["revoked"] == 2


def test_list_sessions_endpoint(fake_auth_service, client: TestClient) -> None:
    user_id = uuid4()
    session_id = uuid4()
    session = UserSession(
        id=session_id,
        user_id=user_id,
        tenant_id=uuid4(),
        refresh_jti="jti-1",
        fingerprint="fp==",
        ip_hash="hash",
        ip_masked="203.0.113.*",
        user_agent="pytest-agent",
        client=SessionClientDetails(platform="macOS", browser="Arc", device="desktop"),
        location=SessionLocation(city="Seattle", region="WA", country="US"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        revoked_at=None,
    )
    fake_auth_service.list_user_sessions.return_value = UserSessionListResult(
        sessions=[session],
        total=1,
    )
    token, _ = _mint_user_token(token_use="access", session_id=session_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/sessions", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["sessions"][0]["id"] == str(session_id)
    assert body["sessions"][0]["current"] is True
    fake_auth_service.list_user_sessions.assert_awaited_once()


def test_delete_session_endpoint(fake_auth_service, client: TestClient) -> None:
    session_id = uuid4()
    fake_auth_service.revoke_user_session_by_id.return_value = True
    token, _ = _mint_user_token(token_use="access")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers)

    assert response.status_code == 200, response.text
    fake_auth_service.revoke_user_session_by_id.assert_awaited_once()
    kwargs = fake_auth_service.revoke_user_session_by_id.await_args.kwargs
    assert kwargs["session_id"] == session_id


def test_delete_session_not_found(fake_auth_service, client: TestClient) -> None:
    fake_auth_service.revoke_user_session_by_id.return_value = False
    token, _ = _mint_user_token(token_use="access")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/api/v1/auth/sessions/{uuid4()}", headers=headers)

    assert response.status_code == 404


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
    assert body["error"] == "Unauthorized"
    assert body["message"] == "Access token required."


def test_password_change_endpoint(fake_auth_service, fake_user_service, client: TestClient) -> None:
    token, subject = _mint_user_token(token_use="access")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "current_password": "CurrentPass!!11",
        "new_password": "AuroraCypress!!992",
    }

    response = client.post("/api/v1/auth/password/change", json=payload, headers=headers)

    assert response.status_code == 200, response.text
    fake_user_service.change_password.assert_awaited_once()
    fake_auth_service.revoke_user_sessions.assert_awaited_once()
    args = fake_user_service.change_password.await_args.kwargs
    assert args["current_password"] == payload["current_password"]
    assert args["new_password"] == payload["new_password"]
    assert args["user_id"]
    revoked_args = fake_auth_service.revoke_user_sessions.await_args
    assert revoked_args.kwargs["reason"] == "password_change"


def test_password_reset_endpoint(fake_auth_service, fake_user_service, client: TestClient) -> None:
    tenant_id = str(uuid4())
    token, _ = _mint_user_token(
        token_use="access",
        scope="support:read",
        tenant_id=tenant_id,
    )
    headers = {"Authorization": f"Bearer {token}"}
    target_user = str(uuid4())
    payload = {
        "user_id": target_user,
        "new_password": "HarborNebula##713",
    }

    response = client.post("/api/v1/auth/password/reset", json=payload, headers=headers)

    assert response.status_code == 200, response.text
    fake_user_service.admin_reset_password.assert_awaited_once()
    kwargs = fake_user_service.admin_reset_password.await_args.kwargs
    assert str(kwargs["target_user_id"]) == target_user
    assert str(kwargs["tenant_id"]) == tenant_id
    assert kwargs["new_password"] == payload["new_password"]
    revoked_args = fake_auth_service.revoke_user_sessions.await_args
    assert revoked_args.kwargs["reason"] == "password_reset"
