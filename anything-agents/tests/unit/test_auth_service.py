"""Unit tests for AuthService service-account issuance."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from datetime import datetime, timezone

from app.domain.auth import RefreshTokenRecord, make_scope_key
from app.core.service_accounts import load_service_account_registry
from app.core.config import get_settings
from app.services.auth_service import (
    AuthService,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
)


class FakeRefreshRepo:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None, str], RefreshTokenRecord] = {}
        self.saved: list[RefreshTokenRecord] = []
        self.revoked: list[str] = []
        self.prefetched: RefreshTokenRecord | None = None

    async def find_active(
        self, account: str, tenant_id: str | None, scopes: list[str]
    ) -> RefreshTokenRecord | None:
        if self.prefetched:
            return self.prefetched
        key = (account, tenant_id, make_scope_key(scopes))
        return self._records.get(key)

    async def save(self, record: RefreshTokenRecord) -> None:
        self.saved.append(record)
        key = (record.account, record.tenant_id, record.scope_key)
        self._records[key] = record

    async def revoke(self, jti: str, *, reason: str | None = None) -> None:
        self.revoked.append(jti)


def _make_service(repo: FakeRefreshRepo | None = None) -> AuthService:
    registry = load_service_account_registry()
    return AuthService(registry, refresh_repository=repo)


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

    settings = get_settings()
    claims = jwt.decode(
        result["refresh_token"],
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert claims["tenant_id"] == tenant_id
    assert claims["scope"] == "conversations:read"
    assert claims["token_use"] == "refresh"
    assert claims["account"] == "analytics-batch"


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
        issued_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        fingerprint=None,
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

    assert result["refresh_token"] == "existing"
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
        issued_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        fingerprint=None,
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

    assert result["refresh_token"] != "existing"
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
    assert saved_record.token == result["refresh_token"]
    assert saved_record.tenant_id == tenant_id
    assert saved_record.scopes == ["conversations:read"]
