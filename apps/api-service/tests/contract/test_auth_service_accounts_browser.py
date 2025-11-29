"""Contract tests for the browser issuance bridge endpoint."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.core.config import get_settings
from app.core.security import get_token_signer
from app.services.service_account_bridge import (
    BrowserIssuanceError,
    get_service_account_issuance_bridge,
)
from main import app


@pytest.fixture(autouse=True)
def clear_overrides() -> Generator[None, None, None]:
    original = dict(app.dependency_overrides)
    try:
        yield
    finally:
        app.dependency_overrides = original


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _mint_access_token(*, tenant_id: str, roles: list[str]) -> str:
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
        "tenant_id": tenant_id,
        "roles": roles,
    }
    return signer.sign(payload).primary.token


def _headers(*, token: str, tenant_id: str, tenant_role: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": tenant_role,
    }


def test_browser_issue_success(client: TestClient) -> None:
    mock_bridge = SimpleNamespace(
        issue_from_browser=AsyncMock(
            return_value={
                "refresh_token": "rt",
                "expires_at": "2025-01-01T00:00:00Z",
                "issued_at": "2025-01-01T00:00:00Z",
                "scopes": ["conversations:read"],
                "tenant_id": "tenant-1",
                "kid": "kid-1",
                "account": "ci",
                "token_use": "refresh",
                "session_id": None,
            }
        )
    )
    app.dependency_overrides[get_service_account_issuance_bridge] = lambda: mock_bridge

    tenant_id = str(uuid4())
    token = _mint_access_token(tenant_id=tenant_id, roles=["admin"])

    response = client.post(
        "/api/v1/auth/service-accounts/browser-issue",
        json={
            "account": "ci",
            "scopes": ["conversations:read"],
            "tenant_id": tenant_id,
            "lifetime_minutes": 60,
            "fingerprint": "runner-1",
            "force": False,
            "reason": "Rotating CI token",
        },
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    mock_bridge.issue_from_browser.assert_awaited_once()
    body = response.json()
    assert body["account"] == "ci"


def test_browser_issue_requires_admin_role(client: TestClient) -> None:
    tenant_id = str(uuid4())
    token = _mint_access_token(tenant_id=tenant_id, roles=["viewer"])

    response = client.post(
        "/api/v1/auth/service-accounts/browser-issue",
        json={
            "account": "ci",
            "scopes": ["conversations:read"],
            "tenant_id": tenant_id,
            "reason": "Rotate token",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_browser_issue_surfaces_service_error(client: TestClient) -> None:
    mock_bridge = SimpleNamespace(
        issue_from_browser=AsyncMock(
            side_effect=BrowserIssuanceError("bad", status.HTTP_400_BAD_REQUEST)
        )
    )
    app.dependency_overrides[get_service_account_issuance_bridge] = lambda: mock_bridge

    tenant_id = str(uuid4())
    token = _mint_access_token(tenant_id=tenant_id, roles=["admin"])

    response = client.post(
        "/api/v1/auth/service-accounts/browser-issue",
        json={
            "account": "ci",
            "scopes": ["conversations:read"],
            "tenant_id": tenant_id,
            "reason": "Rotate token",
        },
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_bridge.issue_from_browser.assert_awaited_once()
