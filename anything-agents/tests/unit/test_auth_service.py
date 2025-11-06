"""Unit tests for AuthService service-account issuance."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from jose import jwt

from app.services.auth_service import (
    AuthService,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
)
from app.core.service_accounts import load_service_account_registry
from app.core.config import get_settings


def _make_service() -> AuthService:
    registry = load_service_account_registry()
    return AuthService(registry)


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
    tasks = [
        service.issue_service_account_refresh_token(
            account="analytics-batch",
            scopes=["conversations:read"],
            tenant_id=tenant_id,
            requested_ttl_minutes=None,
            fingerprint=None,
            force=False,
        )
        for _ in range(5)
    ]
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
