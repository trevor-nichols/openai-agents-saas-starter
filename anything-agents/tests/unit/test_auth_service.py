"""Unit tests for AuthService service-account issuance."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest

from app.core.security import get_token_verifier
from app.core.service_accounts import load_service_account_registry
from app.domain.auth import RefreshTokenRecord, make_scope_key
from app.services.auth_service import (
    AuthService,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    UserAuthenticationError,
)
from app.services.user_service import MembershipNotFoundError, UserService


class FakeRefreshRepo:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None, str], RefreshTokenRecord] = {}
        self.saved: list[RefreshTokenRecord] = []
        self.revoked: list[str] = []
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


def _make_service(repo: FakeRefreshRepo | None = None) -> AuthService:
    registry = load_service_account_registry()
    return AuthService(registry, refresh_repository=repo)


class _StubUserService:
    def __init__(self, *, exc: Exception | None = None) -> None:
        self._exc = exc

    async def authenticate(self, **_: object):
        if self._exc is not None:
            raise self._exc
        raise AssertionError("authenticate should not be called without configured behavior")


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
    assert result["kid"] == "ed25519-active-test"


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
    service = AuthService(load_service_account_registry())

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
    )

    with pytest.raises(UserAuthenticationError):
        await service.login_user(
            email="owner@example.com",
            password="Password123!!",
            tenant_id=tenant_id,
            ip_address=None,
            user_agent=None,
        )
