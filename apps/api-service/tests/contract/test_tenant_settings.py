"""Contract tests for tenant settings API endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.core.security import get_token_signer
from app.domain.feature_flags import FeatureKey, tenant_feature_key
from app.domain.tenant_settings import (
    BillingContact,
    TenantSettingsConflictError,
    TenantSettingsSnapshot,
)
from app.services.tenant.tenant_settings_service import TenantSettingsValidationError
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as http_client:
        yield http_client


@pytest.fixture(autouse=True)
def mock_service(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.tenant.tenant_settings_service.get_tenant_settings_service",
        lambda: mock,
    )
    return mock


def _mint_token(*, tenant_id: str, roles: list[str], scopes: list[str]) -> str:
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
        "tenant_id": tenant_id,
        "roles": roles,
        "scope": " ".join(scopes),
        "email_verified": True,
    }
    return signer.sign(payload).primary.token


def _headers(
    *, token: str, tenant_id: str, tenant_role: str, if_match: str | None = None
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": tenant_role,
    }
    if if_match is not None:
        headers["If-Match"] = if_match
    return headers


def test_get_settings_returns_snapshot(client: TestClient, mock_service: AsyncMock) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["admin"], scopes=["billing:manage"])
    mock_service.get_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(
            tenant_id=tenant_id,
            billing_contacts=[
                BillingContact(name="Ava", email="ava@example.com", notify_billing=True)
            ],
            billing_webhook_url="https://hooks.example.com/tenant",
            plan_metadata={"plan": "pro"},
            flags={"beta": True},
            version=2,
            updated_at=datetime.now(UTC),
        )
    )

    response = client.get(
        "/api/v1/tenants/settings",
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert response.headers.get("ETag") == '"2"'
    mock_service.get_settings.assert_awaited_once_with(tenant_id)


def test_update_settings_persists_payload(client: TestClient, mock_service: AsyncMock) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["owner"], scopes=["billing:manage"])
    mock_service.get_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(tenant_id=tenant_id, flags={}, version=3)
    )
    mock_service.update_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(
            tenant_id=tenant_id,
            billing_contacts=[
                BillingContact(name="Owner", email="owner@example.com", notify_billing=True)
            ],
            billing_webhook_url="https://hooks.example.com/tenant",
            plan_metadata={"plan": "enterprise"},
            flags={"beta": False},
            updated_at=datetime.now(UTC),
        )
    )

    payload = {
        "billing_contacts": [
            {"name": "Owner", "email": "owner@example.com", "notify_billing": True}
        ],
        "billing_webhook_url": "https://hooks.example.com/tenant",
        "plan_metadata": {"plan": "enterprise"},
        "flags": {"beta": False},
    }

    response = client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=_headers(
            token=token, tenant_id=tenant_id, tenant_role="owner", if_match='"3"'
        ),
    )

    assert response.status_code == 200, response.text
    mock_service.update_settings.assert_awaited_once()
    _, kwargs = mock_service.update_settings.call_args
    assert kwargs["expected_version"] == 3


def test_update_settings_translates_validation_error(
    client: TestClient, mock_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["admin"], scopes=["billing:manage"])
    mock_service.get_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(tenant_id=tenant_id, flags={}, version=1)
    )
    mock_service.update_settings = AsyncMock(side_effect=TenantSettingsValidationError("invalid"))

    payload = {
        "billing_contacts": [
            {"name": "Owner", "email": "owner@example.com", "notify_billing": True}
        ],
        "billing_webhook_url": "https://hooks.example.com/tenant",
        "plan_metadata": {"plan": "enterprise"},
        "flags": {"beta": True},
    }

    response = client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=_headers(
            token=token, tenant_id=tenant_id, tenant_role="admin", if_match='"1"'
        ),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "BadRequest"
    assert body["message"] == "invalid"


def test_update_settings_passes_payload_flags_to_service(
    client: TestClient, mock_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["admin"], scopes=["billing:manage"])
    reserved_key = tenant_feature_key(FeatureKey.BILLING)
    mock_service.update_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(tenant_id=tenant_id)
    )

    payload = {
        "billing_contacts": [
            {"name": "Owner", "email": "owner@example.com", "notify_billing": True}
        ],
        "billing_webhook_url": "https://hooks.example.com/tenant",
        "plan_metadata": {"plan": "enterprise"},
        "flags": {reserved_key: False, "beta": True},
    }

    response = client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=_headers(
            token=token, tenant_id=tenant_id, tenant_role="admin", if_match='"4"'
        ),
    )

    assert response.status_code == 200, response.text
    args = mock_service.update_settings.call_args
    assert args is not None
    _, kwargs = args
    assert kwargs["flags"][reserved_key] is False
    assert kwargs["flags"]["beta"] is True


def test_update_settings_requires_if_match(
    client: TestClient, mock_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["owner"], scopes=["billing:manage"])
    mock_service.get_settings = AsyncMock(
        return_value=TenantSettingsSnapshot(tenant_id=tenant_id, flags={}, version=2)
    )

    payload: dict[str, object] = {
        "billing_contacts": [],
        "billing_webhook_url": None,
        "plan_metadata": {},
        "flags": {},
    }

    response = client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="owner"),
    )

    assert response.status_code == 428, response.text
    body = response.json()
    assert body["message"] == "Missing If-Match header with tenant settings version."


def test_update_settings_returns_conflict_on_version_mismatch(
    client: TestClient, mock_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["owner"], scopes=["billing:manage"])
    mock_service.update_settings = AsyncMock(
        side_effect=TenantSettingsConflictError(
            "Tenant settings version conflict; refresh and retry."
        )
    )

    payload: dict[str, object] = {
        "billing_contacts": [],
        "billing_webhook_url": None,
        "plan_metadata": {},
        "flags": {},
    }

    response = client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=_headers(
            token=token, tenant_id=tenant_id, tenant_role="owner", if_match='"4"'
        ),
    )

    assert response.status_code == 409, response.text
    body = response.json()
    assert body["message"] == "Tenant settings version conflict; refresh and retry."
    mock_service.update_settings.assert_awaited_once()
    _, kwargs = mock_service.update_settings.call_args
    assert kwargs["expected_version"] == 4


def test_viewer_forbidden(client: TestClient) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["viewer"], scopes=["billing:read"])

    response = client.get(
        "/api/v1/tenants/settings",
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="viewer"),
    )

    assert response.status_code == 403
