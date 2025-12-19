from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import routes_mfa as mfa_module
from app.api.v1.auth.routes_mfa import router as mfa_router
from app.core.security import get_token_signer
from app.core.settings import get_settings
from app.domain.auth import UserSessionTokens


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    app.include_router(mfa_router, prefix="/api/v1")

    # Stub rate limiter to capture keys
    calls: dict[str, list[str]] = {}

    async def fake_enforce(quota, keys):  # pragma: no cover - simple stub
        calls[quota.scope] = keys

    monkeypatch.setattr(mfa_module.rate_limiter, "enforce", fake_enforce)

    # Stub MFA completion to avoid hitting real service
    async def fake_complete_mfa_challenge(**_: object) -> UserSessionTokens:  # pragma: no cover
        now = datetime.now(UTC)
        return UserSessionTokens(
            access_token="atk",
            refresh_token="rtk",
            expires_at=now + timedelta(minutes=30),
            refresh_expires_at=now + timedelta(days=7),
            kid="kid",
            refresh_kid="rkid",
            scopes=[],
            tenant_id="tenant",
            user_id="user",
            email_verified=True,
            session_id=str(uuid4()),
        )

    # Avoid instantiating real AuthService (needs DB); patch module-level reference directly
    class _StubAuth:
        async def complete_mfa_challenge(self, **kwargs: object) -> UserSessionTokens:  # pragma: no cover
            return await fake_complete_mfa_challenge(**kwargs)

    monkeypatch.setattr(mfa_module, "auth_service", _StubAuth())

    client = TestClient(app)
    client._rate_limit_calls = calls  # type: ignore[attr-defined]
    return client


def _make_challenge_token(user_id: UUID) -> str:
    """Create a minimally valid MFA challenge token using the real signer."""

    settings = get_settings()
    signer = get_token_signer(settings)
    issued_at = datetime.now(UTC)
    payload = {
        "sub": f"user:{user_id}",
        "tenant_id": str(uuid4()),
        "token_use": "mfa_challenge",
        "iss": settings.app_name,
        "aud": settings.auth_audience or [settings.app_name],
        "jti": str(uuid4()),
        "sid": str(uuid4()),
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=5)).timestamp()),
    }
    return signer.sign(payload).primary.token


def test_mfa_complete_rate_limited_by_user_not_method(client: TestClient) -> None:
    user_id = uuid4()
    method_id = uuid4()
    challenge = _make_challenge_token(user_id)

    resp = client.post(
        "/api/v1/mfa/complete",
        json={
            "challenge_token": challenge,
            "method_id": str(method_id),
            "code": "123456",
        },
    )

    assert resp.status_code == 200
    calls = client._rate_limit_calls  # type: ignore[attr-defined]
    assert "user" in calls
    assert str(user_id) in calls["user"]
    assert str(method_id) not in calls["user"]
    # IP quota also enforced; presence of any value is fine, but ensure it ran
    assert "ip" in calls
