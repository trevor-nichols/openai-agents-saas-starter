"""Unit tests for AuthService service-account issuance."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from types import MethodType
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.core.keys import load_keyset
from app.core.security import get_token_verifier
from app.core.service_accounts import load_service_account_registry
from app.domain.auth import (
    RefreshTokenRecord,
    ServiceAccountTokenListResult,
    ServiceAccountTokenStatus,
    ServiceAccountTokenView,
    SessionClientDetails,
    UserSession,
    UserSessionListResult,
    make_scope_key,
)
from app.services.auth.mfa_service import MfaService
from app.services.auth_service import (
    AuthService,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    UserAuthenticationError,
    UserLogoutError,
)
from app.services.users import MembershipNotFoundError, UserService


class FakeRefreshRepo:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None, str], RefreshTokenRecord] = {}
        self.saved: list[RefreshTokenRecord] = []
        self.revoked: list[str] = []
        self.revoked_accounts: list[str] = []
        self.prefetched: RefreshTokenRecord | None = None

    async def find_active(
        self, account: str, tenant_id: str | None, scopes: Sequence[str]
    ) -> RefreshTokenRecord | None:
        if self.prefetched:
            return self.prefetched
        key = (account, tenant_id, make_scope_key(scopes))
        return self._records.get(key)

    async def get_by_jti(self, jti: str) -> RefreshTokenRecord | None:
        if self.prefetched and self.prefetched.jti == jti:
            return self.prefetched
        for record in self._records.values():
            if record.jti == jti:
                return record
        return None

    async def save(self, record: RefreshTokenRecord) -> None:
        self.saved.append(record)
        key = (record.account, record.tenant_id, record.scope_key)
        self._records[key] = record

    async def revoke(self, jti: str, *, reason: str | None = None) -> None:
        self.revoked.append(jti)

    async def revoke_account(self, account: str, *, reason: str | None = None) -> int:
        victims = [key for key in self._records if key[0] == account]
        for key in victims:
            del self._records[key]
        self.revoked_accounts.append(account)
        return len(victims)

    async def list_service_account_tokens(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
        limit: int,
        offset: int,
    ) -> ServiceAccountTokenListResult:
        tokens = [
            ServiceAccountTokenView(
                jti=record.jti,
                account=record.account,
                tenant_id=record.tenant_id,
                scopes=record.scopes,
                expires_at=record.expires_at,
                issued_at=record.issued_at,
                revoked_at=None,
                revoked_reason=None,
                fingerprint=record.fingerprint,
                signing_kid=record.signing_kid or "unknown",
            )
            for record in self._records.values()
        ]
        return ServiceAccountTokenListResult(tokens=tokens, total=len(tokens))


def _make_service(
    repo: FakeRefreshRepo | None = None,
    session_repo: FakeSessionRepo | None = None,
    user_service: UserService | None = None,
) -> AuthService:
    registry = load_service_account_registry()
    resolved_user_service = user_service or _NoopUserService()
    return AuthService(
        registry,
        refresh_repository=repo,
        session_repository=session_repo,
        user_service=cast(UserService, resolved_user_service),
        mfa_service=cast(MfaService, _StubMfaService()),
    )


class FakeSessionRepo:
    def __init__(self) -> None:
        self.sessions: dict[UUID, UserSession] = {}
        self.list_result = UserSessionListResult(sessions=[], total=0)
        self.revoked_sessions: list[UUID] = []
        self.revoked_users: list[UUID] = []
        self.revoked_jtis: list[str] = []

    async def upsert_session(self, **_: object) -> UserSession:
        raise AssertionError("not expected in these tests")

    async def list_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None = None,
        include_revoked: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> UserSessionListResult:
        return self.list_result

    async def get_session(self, *, session_id: UUID, user_id: UUID) -> UserSession | None:
        session = self.sessions.get(session_id)
        if session and session.user_id == user_id:
            return session
        return None

    async def mark_session_revoked(self, *, session_id: UUID, reason: str | None = None) -> bool:
        self.revoked_sessions.append(session_id)
        return True

    async def mark_session_revoked_by_jti(
        self, *, refresh_jti: str, reason: str | None = None
    ) -> bool:
        self.revoked_jtis.append(refresh_jti)
        return True

    async def revoke_all_for_user(self, *, user_id: UUID, reason: str | None = None) -> int:
        self.revoked_users.append(user_id)
        return sum(1 for session in self.sessions.values() if session.user_id == user_id)


class _StubUserService:
    def __init__(self, *, exc: Exception | None = None) -> None:
        self._exc = exc

    async def authenticate(self, **_: object):
        if self._exc is not None:
            raise self._exc
        raise AssertionError("authenticate should not be called without configured behavior")


class _NoopUserService:
    async def authenticate(self, **_: object):  # pragma: no cover - guardrail
        raise AssertionError("UserService should not be used in this test.")

    async def load_active_user(self, **_: object):  # pragma: no cover - guardrail
        raise AssertionError("UserService should not be used in this test.")

    async def record_login_success(self, **_: object):  # pragma: no cover - guardrail
        raise AssertionError("UserService should not be used in this test.")


class _StubMfaService:
    async def list_methods(self, *_: object):  # pragma: no cover - guardrail
        raise AssertionError("MfaService should not be used in this test.")

    async def verify_totp(self, *_: object, **__: object):  # pragma: no cover - guardrail
        raise AssertionError("MfaService should not be used in this test.")


def _refresh_token(payload: Mapping[str, object]) -> str:
    token = payload.get("refresh_token")
    assert isinstance(token, str), "refresh_token should be issued as a string"
    return token


def test_service_account_registry_loads_defaults() -> None:
    registry = load_service_account_registry()
    accounts = list(registry.accounts())
    assert "analytics-batch" in accounts


@pytest.mark.asyncio
async def test_issue_service_account_refresh_token_success() -> None:
    service = _make_service()
    tenant_id = "11111111-2222-3333-4444-555555555555"

    result = await service.issue_service_account_refresh_token(
        account="analytics-batch",
        scopes=["conversations:read"],
        tenant_id=tenant_id,
        requested_ttl_minutes=60,
        fingerprint="ci-runner-1",
        force=False,
    )

    assert result["account"] == "analytics-batch"
    assert result["tenant_id"] == tenant_id
    assert result["scopes"] == ["conversations:read"]
    assert result["token_use"] == "refresh"

    claims = get_token_verifier().verify(_refresh_token(result))

    assert claims["tenant_id"] == tenant_id
    assert claims["scope"] == "conversations:read"
    assert claims["token_use"] == "refresh"
    assert claims["account"] == "analytics-batch"
    keyset = load_keyset()
    assert keyset.active is not None
    assert result["kid"] == keyset.active.kid


@pytest.mark.asyncio
async def test_issue_requires_tenant_for_tenant_bound_account() -> None:
    service = _make_service()

    with pytest.raises(ServiceAccountValidationError):
        await service.issue_service_account_refresh_token(
            account="analytics-batch",
            scopes=["conversations:read"],
            tenant_id=None,
            requested_ttl_minutes=None,
            fingerprint=None,
            force=False,
        )


@pytest.mark.asyncio
async def test_issue_rejects_invalid_scopes() -> None:
    service = _make_service()
    tenant_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    with pytest.raises(ServiceAccountValidationError):
        await service.issue_service_account_refresh_token(
            account="analytics-batch",
            scopes=["billing:read"],
            tenant_id=tenant_id,
            requested_ttl_minutes=None,
            fingerprint=None,
            force=False,
        )


@pytest.mark.asyncio
async def test_rate_limit_enforced_per_account(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _make_service()
    tenant_id = "ffffffff-1111-2222-3333-444444444444"

    # Ensure we start with clean rate limit state by creating a fresh AuthService.
    service = _make_service()

    # Consume 5 successful requests.
    tasks = []
    for _ in range(5):
        tasks.append(
            service.issue_service_account_refresh_token(
                account="analytics-batch",
                scopes=["conversations:read"],
                tenant_id=tenant_id,
                requested_ttl_minutes=None,
                fingerprint=None,
                force=False,
            )
        )
    await asyncio.gather(*tasks)

    with pytest.raises(ServiceAccountRateLimitError):
        await service.issue_service_account_refresh_token(
            account="analytics-batch",
            scopes=["conversations:read"],
            tenant_id=tenant_id,
            requested_ttl_minutes=None,
            fingerprint=None,
            force=False,
        )


@pytest.mark.asyncio
async def test_existing_token_reused_when_available() -> None:
    repo = FakeRefreshRepo()
    record = RefreshTokenRecord(
        token="existing",
        jti="existing-jti",
        account="analytics-batch",
        tenant_id="11111111-2222-3333-4444-555555555555",
        scopes=["conversations:read"],
        issued_at=datetime.now(UTC) - timedelta(minutes=1),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        fingerprint=None,
        signing_kid="ed25519-active-test",
    )
    repo.prefetched = record
    service = _make_service(repo)

    result = await service.issue_service_account_refresh_token(
        account="analytics-batch",
        scopes=["conversations:read"],
        tenant_id=record.tenant_id,
        requested_ttl_minutes=None,
        fingerprint=None,
        force=False,
    )

    assert _refresh_token(result) == "existing"
    assert repo.saved == []


@pytest.mark.asyncio
async def test_force_override_mints_new_token() -> None:
    repo = FakeRefreshRepo()
    record = RefreshTokenRecord(
        token="existing",
        jti="existing-jti",
        account="analytics-batch",
        tenant_id="11111111-2222-3333-4444-555555555555",
        scopes=["conversations:read"],
        issued_at=datetime.now(UTC) - timedelta(minutes=1),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        fingerprint=None,
        signing_kid="ed25519-active-test",
    )
    repo.prefetched = record
    service = _make_service(repo)

    result = await service.issue_service_account_refresh_token(
        account="analytics-batch",
        scopes=["conversations:read"],
        tenant_id=record.tenant_id,
        requested_ttl_minutes=None,
        fingerprint=None,
        force=True,
    )

    assert _refresh_token(result) != "existing"
    assert len(repo.saved) == 1


@pytest.mark.asyncio
async def test_new_token_persisted_to_repository() -> None:
    repo = FakeRefreshRepo()
    service = _make_service(repo)
    tenant_id = "11111111-2222-3333-4444-555555555555"

    result = await service.issue_service_account_refresh_token(
        account="analytics-batch",
        scopes=["conversations:read"],
        tenant_id=tenant_id,
        requested_ttl_minutes=15,
        fingerprint="fp",
        force=False,
    )

    assert repo.saved, "Expected token to be persisted"
    saved_record = repo.saved[-1]
    assert saved_record.token == _refresh_token(result)
    assert saved_record.tenant_id == tenant_id
    assert saved_record.scopes == ["conversations:read"]
    assert saved_record.signing_kid == result["kid"]


@pytest.mark.asyncio
async def test_login_user_handles_membership_not_found() -> None:
    tenant_id = str(uuid4())
    stub = _StubUserService(exc=MembershipNotFoundError("not a member"))
    service = AuthService(
        load_service_account_registry(),
        refresh_repository=None,
        user_service=cast(UserService, stub),
        mfa_service=cast(MfaService, _StubMfaService()),
    )

    with pytest.raises(UserAuthenticationError):
        await service.login_user(
            email="owner@example.com",
            password="MapleSunder##552",
            tenant_id=tenant_id,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_revoke_user_sessions_delegates_to_refresh_repo() -> None:
    repo = FakeRefreshRepo()
    service = _make_service(repo)
    user_id = uuid4()
    account = f"user:{user_id}"
    record = RefreshTokenRecord(
        token="token-1",
        jti="jti-1",
        account=account,
        tenant_id=None,
        scopes=["conversations:read"],
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        fingerprint=None,
        signing_kid="kid-1",
    )
    repo._records[(account, None, make_scope_key(record.scopes))] = record

    revoked = await service.revoke_user_sessions(user_id, reason="password_reset")

    assert revoked == 1
    assert repo.revoked_accounts == [account]


@pytest.mark.asyncio
async def test_logout_user_session_revokes_matching_token(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = FakeRefreshRepo()
    service = _make_service(repo)
    user_id = uuid4()
    account = f"user:{user_id}"
    record = RefreshTokenRecord(
        token="token-1",
        jti="jti-1",
        account=account,
        tenant_id="tenant-1",
        scopes=["conversations:read"],
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        fingerprint="fp",
        signing_kid="kid-1",
    )
    repo._records[(account, record.tenant_id, make_scope_key(record.scopes))] = record

    def _fake_verify(self, *_: object, **__: object):
        return {"token_use": "refresh", "sub": f"user:{user_id}", "jti": record.jti}

    monkeypatch.setattr(service, "_verify_token", MethodType(_fake_verify, service))

    revoked = await service.logout_user_session(
        refresh_token="token-1",
        expected_user_id=str(user_id),
    )

    assert revoked is True
    assert repo.revoked == [record.jti]


@pytest.mark.asyncio
async def test_logout_user_session_is_idempotent_when_record_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FakeRefreshRepo()
    service = _make_service(repo)
    user_id = uuid4()

    def _fake_verify(self, *_: object, **__: object):
        return {"token_use": "refresh", "sub": f"user:{user_id}", "jti": "unknown"}

    monkeypatch.setattr(service, "_verify_token", MethodType(_fake_verify, service))

    revoked = await service.logout_user_session(
        refresh_token="token-unknown",
        expected_user_id=str(user_id),
    )

    assert revoked is False
    assert repo.revoked == []


@pytest.mark.asyncio
async def test_logout_user_session_rejects_mismatched_user(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = FakeRefreshRepo()
    service = _make_service(repo)
    owner_id = uuid4()
    foreign_id = uuid4()

    def _fake_verify(self, *_: object, **__: object):
        return {"token_use": "refresh", "sub": f"user:{foreign_id}", "jti": "jti-1"}

    monkeypatch.setattr(service, "_verify_token", MethodType(_fake_verify, service))

    with pytest.raises(UserLogoutError):
        await service.logout_user_session(
            refresh_token="token-foreign",
            expected_user_id=str(owner_id),
        )


def _build_session(
    *,
    session_id: UUID,
    user_id: UUID,
    tenant_id: UUID | None = None,
    refresh_jti: str = 'jti-test',
) -> UserSession:
    now = datetime.now(UTC)
    return UserSession(
        id=session_id,
        user_id=user_id,
        tenant_id=tenant_id or uuid4(),
        refresh_jti=refresh_jti,
        fingerprint=None,
        ip_hash=None,
        ip_masked='203.0.113.*',
        user_agent='pytest-agent',
        client=SessionClientDetails(),
        location=None,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
        revoked_at=None,
    )


@pytest.mark.asyncio
async def test_revoke_user_session_by_id_revokes_refresh_and_session() -> None:
    refresh_repo = FakeRefreshRepo()
    session_repo = FakeSessionRepo()
    service = _make_service(refresh_repo, session_repo)
    user_id = uuid4()
    session_id = uuid4()
    session_repo.sessions[session_id] = _build_session(
        session_id=session_id,
        user_id=user_id,
        tenant_id=uuid4(),
        refresh_jti='jti-session',
    )

    result = await service.revoke_user_session_by_id(user_id=user_id, session_id=session_id)

    assert result is True
    assert 'jti-session' in refresh_repo.revoked
    assert session_id in session_repo.revoked_sessions


@pytest.mark.asyncio
async def test_revoke_user_session_by_id_returns_false_when_missing() -> None:
    service = _make_service(FakeRefreshRepo(), FakeSessionRepo())
    assert (
        await service.revoke_user_session_by_id(user_id=uuid4(), session_id=uuid4()) is False
    )


@pytest.mark.asyncio
async def test_list_user_sessions_delegates_to_repository() -> None:
    repo = FakeSessionRepo()
    expected = UserSessionListResult(sessions=[], total=0)
    repo.list_result = expected
    service = _make_service(FakeRefreshRepo(), repo)

    result = await service.list_user_sessions(user_id=uuid4())

    assert result is expected
