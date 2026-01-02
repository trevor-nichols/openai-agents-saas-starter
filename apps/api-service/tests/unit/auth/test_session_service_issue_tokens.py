"""Unit tests for UserSessionService token issuance wiring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.domain.tenant_roles import TenantRole
from app.domain.users import AuthenticatedUser
from app.services.auth.mfa_service import MfaService
from app.services.auth.refresh_token_manager import RefreshTokenManager
from app.services.auth.session_service import UserSessionService
from app.services.auth.session_store import SessionStore
from app.services.auth.session_token_issuer import IssuedSessionTokens
from app.services.users import UserService


class _FakeSessionStore:
    def __init__(self) -> None:
        self.upsert_calls: list[dict[str, object]] = []

    async def upsert(self, **kwargs: object) -> None:
        self.upsert_calls.append(kwargs)


class _FakeRefreshTokens:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []

    async def save(self, **kwargs: object) -> None:
        self.saved.append(kwargs)


class _StubUserService:
    def __init__(self, auth_user: AuthenticatedUser) -> None:
        self._auth_user = auth_user
        self.login_success_called = False
        self.login_success_reason: str | None = None

    async def authenticate(self, **_: object):  # pragma: no cover - guardrail
        raise AssertionError("UserService should not be used in this test.")

    async def load_active_user(self, **_: object) -> AuthenticatedUser:
        return self._auth_user

    async def record_login_success(self, **_: object) -> None:
        self.login_success_called = True
        reason = _.get("reason")
        self.login_success_reason = reason if isinstance(reason, str) else None


class _StubMfaService:
    async def list_methods(self, *_: object):  # pragma: no cover - guardrail
        return []

    async def verify_totp(self, *_: object, **__: object):  # pragma: no cover - guardrail
        raise AssertionError("MfaService should not be used in this test.")


class _StubMfaVerifyService:
    async def list_methods(self, *_: object):  # pragma: no cover - guardrail
        return []

    async def verify_totp(self, *_: object, **__: object) -> None:
        return None


@pytest.mark.asyncio
async def test_issue_user_tokens_persists_session_and_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    issued_at = datetime.now(UTC)
    access_expires = issued_at + timedelta(minutes=15)
    refresh_expires = issued_at + timedelta(days=30)
    session_id = uuid4()
    refresh_jti = "refresh-jti"
    account = f"user:{user_id}"

    issued = IssuedSessionTokens(
        access_token="access-token",
        refresh_token="refresh-token",
        access_expires_at=access_expires,
        refresh_expires_at=refresh_expires,
        access_kid="kid-access",
        refresh_kid="kid-refresh",
        access_jti="access-jti",
        refresh_jti=refresh_jti,
        session_id=session_id,
        fingerprint="fp",
        account=account,
        issued_at=issued_at,
    )

    def _issue_stub(*_: object, **__: object) -> IssuedSessionTokens:
        return issued

    from app.services.auth import session_service as session_service_module

    monkeypatch.setattr(session_service_module, "issue_session_tokens", _issue_stub)

    auth_user = AuthenticatedUser(
        user_id=user_id,
        tenant_id=tenant_id,
        email="user@example.com",
        role=TenantRole.MEMBER,
        scopes=["conversations:read"],
        email_verified=True,
    )
    session_store = _FakeSessionStore()
    refresh_tokens = _FakeRefreshTokens()
    service = UserSessionService(
        refresh_tokens=cast(RefreshTokenManager, refresh_tokens),
        session_store=cast(SessionStore, session_store),
        user_service=cast(UserService, _StubUserService(auth_user)),
        mfa_service=cast(MfaService, _StubMfaService()),
    )

    result = await service._issue_user_tokens(
        auth_user,
        ip_address="1.2.3.4",
        user_agent="TestAgent",
        reason="login",
    )

    assert result.access_token == issued.access_token
    assert result.refresh_token == issued.refresh_token
    assert result.kid == issued.access_kid
    assert result.refresh_kid == issued.refresh_kid
    assert result.refresh_expires_at == issued.refresh_expires_at
    assert result.session_id == str(issued.session_id)

    assert len(session_store.upsert_calls) == 1
    upsert_call = session_store.upsert_calls[0]
    assert upsert_call["session_id"] == issued.session_id
    assert upsert_call["refresh_jti"] == issued.refresh_jti
    assert upsert_call["fingerprint"] == issued.fingerprint
    assert upsert_call["ip_address"] == "1.2.3.4"
    assert upsert_call["user_agent"] == "TestAgent"
    assert upsert_call["occurred_at"] == issued.issued_at

    assert len(refresh_tokens.saved) == 1
    save_call = refresh_tokens.saved[0]
    assert save_call["token"] == issued.refresh_token
    assert save_call["account"] == issued.account
    assert save_call["issued_at"] == issued.issued_at
    assert save_call["expires_at"] == issued.refresh_expires_at
    assert save_call["signing_kid"] == issued.refresh_kid
    assert save_call["session_id"] == issued.session_id
    assert save_call["jti"] == issued.refresh_jti


@pytest.mark.asyncio
async def test_issue_tokens_for_user_uses_issuer_and_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    issued_at = datetime.now(UTC)
    access_expires = issued_at + timedelta(minutes=15)
    refresh_expires = issued_at + timedelta(days=30)
    session_id = uuid4()

    issued = IssuedSessionTokens(
        access_token="access-token",
        refresh_token="refresh-token",
        access_expires_at=access_expires,
        refresh_expires_at=refresh_expires,
        access_kid="kid-access",
        refresh_kid="kid-refresh",
        access_jti="access-jti",
        refresh_jti="refresh-jti",
        session_id=session_id,
        fingerprint="fp",
        account=f"user:{user_id}",
        issued_at=issued_at,
    )

    def _issue_stub(*_: object, **__: object) -> IssuedSessionTokens:
        return issued

    from app.services.auth import session_service as session_service_module

    monkeypatch.setattr(session_service_module, "issue_session_tokens", _issue_stub)

    auth_user = AuthenticatedUser(
        user_id=user_id,
        tenant_id=tenant_id,
        email="user@example.com",
        role=TenantRole.MEMBER,
        scopes=["conversations:read"],
        email_verified=True,
    )
    user_service = _StubUserService(auth_user)
    session_store = _FakeSessionStore()
    refresh_tokens = _FakeRefreshTokens()
    service = UserSessionService(
        refresh_tokens=cast(RefreshTokenManager, refresh_tokens),
        session_store=cast(SessionStore, session_store),
        user_service=cast(UserService, user_service),
        mfa_service=cast(MfaService, _StubMfaService()),
    )

    result = await service.issue_tokens_for_user(
        user_id=user_id,
        tenant_id=tenant_id,
        ip_address="1.2.3.4",
        user_agent="TestAgent",
        reason="sso",
        enforce_mfa=False,
    )

    assert result.access_token == issued.access_token
    assert result.refresh_token == issued.refresh_token
    assert user_service.login_success_called is True
    assert session_store.upsert_calls, "Expected session metadata to be persisted"
    assert refresh_tokens.saved, "Expected refresh token to be persisted"


@pytest.mark.asyncio
async def test_complete_mfa_challenge_records_login_success(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    session_id = uuid4()
    issued_at = datetime.now(UTC)
    issued = IssuedSessionTokens(
        access_token="access-token",
        refresh_token="refresh-token",
        access_expires_at=issued_at + timedelta(minutes=15),
        refresh_expires_at=issued_at + timedelta(days=30),
        access_kid="kid-access",
        refresh_kid="kid-refresh",
        access_jti="access-jti",
        refresh_jti="refresh-jti",
        session_id=session_id,
        fingerprint="fp",
        account=f"user:{user_id}",
        issued_at=issued_at,
    )

    def _issue_stub(*_: object, **__: object) -> IssuedSessionTokens:
        return issued

    from app.services.auth import session_service as session_service_module

    monkeypatch.setattr(session_service_module, "issue_session_tokens", _issue_stub)

    auth_user = AuthenticatedUser(
        user_id=user_id,
        tenant_id=tenant_id,
        email="user@example.com",
        role=TenantRole.MEMBER,
        scopes=["conversations:read"],
        email_verified=True,
    )
    user_service = _StubUserService(auth_user)
    session_store = _FakeSessionStore()
    refresh_tokens = _FakeRefreshTokens()
    payload = {
        "token_use": "mfa_challenge",
        "sub": f"user:{user_id}",
        "tenant_id": str(tenant_id),
        "sid": str(session_id),
        "login_reason": "sso",
    }

    def _verifier(_: str, **__: object) -> dict[str, object]:
        return payload

    service = UserSessionService(
        refresh_tokens=cast(RefreshTokenManager, refresh_tokens),
        session_store=cast(SessionStore, session_store),
        user_service=cast(UserService, user_service),
        token_verifier=_verifier,
        mfa_service=cast(MfaService, _StubMfaVerifyService()),
    )

    result = await service.complete_mfa_challenge(
        challenge_token="challenge",
        method_id=uuid4(),
        code="123456",
        ip_address="1.2.3.4",
        user_agent="TestAgent",
        ip_hash="ip-hash",
        user_agent_hash="ua-hash",
    )

    assert result.access_token == issued.access_token
    assert user_service.login_success_called is True
    assert user_service.login_success_reason == "sso"
