"""Contract tests for service-account token list/revoke endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import get_token_signer
from app.domain.auth import (
    ServiceAccountTokenListResult,
    ServiceAccountTokenStatus,
    ServiceAccountTokenView,
)
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def mock_auth_service(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    mock.list_service_account_tokens = AsyncMock()
    mock.revoke_service_account_token = AsyncMock()
    monkeypatch.setattr(
        "app.api.v1.auth.routes_service_account_tokens.auth_service",
        mock,
    )
    return mock


def _mint_access_token(
    *,
    tenant_id: str | None,
    roles: list[str] | None = None,
    scopes: list[str] | None = None,
) -> str:
    signer = get_token_signer()
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": f"user:{uuid4()}",
        "token_use": "access",
        "iss": settings.app_name,
        "aud": settings.auth_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "email_verified": True,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    if roles:
        payload["roles"] = roles
    if scopes:
        payload["scope"] = " ".join(scopes)
    return signer.sign(payload).primary.token


def _token_headers(
    *,
    token: str,
    tenant_id: str | None = None,
    tenant_role: str | None = None,
    operator_override: bool = False,
    operator_reason: str | None = None,
) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id
    if tenant_role:
        headers["X-Tenant-Role"] = tenant_role
    if operator_override:
        headers["X-Operator-Override"] = "true"
    if operator_reason:
        headers["X-Operator-Reason"] = operator_reason
    return headers


def _sample_token_view(tenant_id: str | None) -> ServiceAccountTokenView:
    now = datetime.now(UTC)
    return ServiceAccountTokenView(
        jti="sample-jti",
        account="analytics-batch",
        tenant_id=tenant_id,
        scopes=["conversations:read"],
        expires_at=now + timedelta(hours=1),
        issued_at=now,
        revoked_at=None,
        revoked_reason=None,
        fingerprint="ci",
        signing_kid="kid-primary",
    )


def test_tenant_admin_list_tokens_scoped(client: TestClient, mock_auth_service: AsyncMock) -> None:
    tenant_id = str(uuid4())
    token = _mint_access_token(tenant_id=tenant_id, roles=["admin"], scopes=["conversations:read"])
    mock_auth_service.list_service_account_tokens.return_value = ServiceAccountTokenListResult(
        tokens=[_sample_token_view(tenant_id)],
        total=1,
    )

    response = client.get(
        "/api/v1/auth/service-accounts/tokens",
        headers=_token_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    mock_auth_service.list_service_account_tokens.assert_awaited_once_with(
        tenant_ids=[tenant_id],
        include_global=False,
        account_query=None,
        fingerprint=None,
        status=ServiceAccountTokenStatus.ACTIVE,
        limit=20,
        offset=0,
    )


def test_operator_list_requires_reason(client: TestClient, mock_auth_service: AsyncMock) -> None:
    token = _mint_access_token(tenant_id=None, scopes=["support:*"])

    response = client.get(
        "/api/v1/auth/service-accounts/tokens",
        headers=_token_headers(token=token, operator_override=True),
    )

    assert response.status_code == 400
    mock_auth_service.list_service_account_tokens.assert_not_called()


def test_operator_list_cross_tenant(client: TestClient, mock_auth_service: AsyncMock) -> None:
    target_tenant = str(uuid4())
    token = _mint_access_token(tenant_id=None, scopes=["support:*"])
    mock_auth_service.list_service_account_tokens.return_value = ServiceAccountTokenListResult(
        tokens=[_sample_token_view(target_tenant)],
        total=1,
    )

    response = client.get(
        f"/api/v1/auth/service-accounts/tokens?tenant_id={target_tenant}&include_global=true",
        headers=_token_headers(
            token=token,
            operator_override=True,
            operator_reason="audit",
        ),
    )

    assert response.status_code == 200
    mock_auth_service.list_service_account_tokens.assert_awaited_with(
        tenant_ids=[target_tenant],
        include_global=True,
        account_query=None,
        fingerprint=None,
        status=ServiceAccountTokenStatus.ACTIVE,
        limit=20,
        offset=0,
    )


def test_tenant_admin_revoke_defaults_reason(
    client: TestClient, mock_auth_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_access_token(tenant_id=tenant_id, roles=["admin"], scopes=["conversations:read"])

    response = client.post(
        "/api/v1/auth/service-accounts/tokens/sample-jti/revoke",
        json={},
        headers=_token_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == 200, response.text
    mock_auth_service.revoke_service_account_token.assert_awaited_once_with(
        "sample-jti",
        reason="tenant_admin_manual_revoke",
    )


def test_operator_revoke_requires_reason(client: TestClient, mock_auth_service: AsyncMock) -> None:
    token = _mint_access_token(tenant_id=None, scopes=["support:*"])

    response = client.post(
        "/api/v1/auth/service-accounts/tokens/sample-jti/revoke",
        json={},
        headers=_token_headers(token=token, operator_override=True),
    )

    assert response.status_code == 400
    mock_auth_service.revoke_service_account_token.assert_not_called()
