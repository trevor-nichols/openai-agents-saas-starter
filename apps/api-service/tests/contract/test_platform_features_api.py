"""Contract tests for platform feature entitlements."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_token_signer
from app.core.settings import get_settings
from app.services.feature_flags.entitlements import get_feature_entitlement_service
from app.services.tenant.tenant_account_service import (
    TenantAccountNotFoundError,
    get_tenant_account_service,
)
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_account_service() -> Generator[AsyncMock, None, None]:
    mock = AsyncMock()
    mock.get_account = AsyncMock()
    app.dependency_overrides[get_tenant_account_service] = lambda: mock
    try:
        yield mock
    finally:
        app.dependency_overrides.pop(get_tenant_account_service, None)


@pytest.fixture
def mock_entitlement_service() -> Generator[AsyncMock, None, None]:
    mock = AsyncMock()
    mock.get_entitlements = AsyncMock()
    mock.update_entitlements = AsyncMock()
    app.dependency_overrides[get_feature_entitlement_service] = lambda: mock
    try:
        yield mock
    finally:
        app.dependency_overrides.pop(get_feature_entitlement_service, None)


def _mint_token(*, scopes: list[str]) -> str:
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
        "roles": [],
        "scope": " ".join(scopes),
    }
    return signer.sign(payload).primary.token


def _operator_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_platform_features_get_returns_404_for_missing_tenant(
    client: TestClient,
    mock_account_service: AsyncMock,
    mock_entitlement_service: AsyncMock,
) -> None:
    tenant_id = uuid4()
    mock_account_service.get_account.side_effect = TenantAccountNotFoundError(
        "Tenant account not found."
    )

    token = _mint_token(scopes=["platform:operator"])
    response = client.get(
        f"/api/v1/platform/tenants/{tenant_id}/features",
        headers=_operator_headers(token),
    )

    assert response.status_code == 404, response.text
    mock_entitlement_service.get_entitlements.assert_not_called()


def test_platform_features_update_returns_404_for_missing_tenant(
    client: TestClient,
    mock_account_service: AsyncMock,
    mock_entitlement_service: AsyncMock,
) -> None:
    tenant_id = uuid4()
    mock_account_service.get_account.side_effect = TenantAccountNotFoundError(
        "Tenant account not found."
    )

    token = _mint_token(scopes=["platform:operator"])
    response = client.put(
        f"/api/v1/platform/tenants/{tenant_id}/features",
        headers=_operator_headers(token),
        json={"flags": {"billing": True}},
    )

    assert response.status_code == 404, response.text
    mock_entitlement_service.update_entitlements.assert_not_called()
