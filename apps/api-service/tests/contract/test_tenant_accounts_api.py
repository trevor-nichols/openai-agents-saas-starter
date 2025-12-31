"""Contract tests for tenant account API endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_token_signer
from app.core.settings import get_settings
from app.domain.tenant_accounts import TenantAccount, TenantAccountListResult, TenantAccountStatus
from app.services.tenant.tenant_lifecycle_service import TenantLifecycleBillingError
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_account_service(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    mock.get_account = AsyncMock()
    mock.update_account = AsyncMock()
    mock.list_accounts = AsyncMock()
    mock.create_account = AsyncMock()
    monkeypatch.setattr(
        "app.services.tenant.tenant_account_service.get_tenant_account_service",
        lambda: mock,
    )
    return mock


@pytest.fixture
def mock_lifecycle_service(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    mock.suspend_tenant = AsyncMock()
    mock.reactivate_tenant = AsyncMock()
    mock.deprovision_tenant = AsyncMock()
    monkeypatch.setattr(
        "app.services.tenant.tenant_lifecycle_service.get_tenant_lifecycle_service",
        lambda: mock,
    )
    return mock


def _mint_token(*, tenant_id: str | None, roles: list[str], scopes: list[str]) -> str:
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
        "roles": roles,
        "scope": " ".join(scopes),
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return signer.sign(payload).primary.token


def _headers(*, token: str, tenant_id: str, tenant_role: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": tenant_role,
    }


def _operator_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _operator_override_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Operator-Override": "true",
        "X-Operator-Reason": "investigation",
    }


def _account(
    tenant_id: UUID,
    *,
    status: TenantAccountStatus = TenantAccountStatus.ACTIVE,
    name: str = "Acme Corp",
) -> TenantAccount:
    now = datetime.now(UTC)
    return TenantAccount(
        id=tenant_id,
        slug=f"tenant-{tenant_id.hex[:8]}",
        name=name,
        status=status,
        created_at=now,
        updated_at=now,
        status_updated_at=now,
        status_updated_by=None,
        status_reason=None,
        suspended_at=now if status == TenantAccountStatus.SUSPENDED else None,
        deprovisioned_at=now if status == TenantAccountStatus.DEPROVISIONED else None,
    )


def test_get_tenant_account_returns_payload(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id)
    mock_account_service.get_account.return_value = account

    token = _mint_token(
        tenant_id=str(tenant_id),
        roles=["owner"],
        scopes=["billing:manage"],
    )

    response = client.get(
        "/api/v1/tenants/account",
        headers=_headers(token=token, tenant_id=str(tenant_id), tenant_role="owner"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(tenant_id)
    assert body["status"] == account.status.value
    assert mock_account_service.get_account.await_count >= 1


def test_update_tenant_account_updates_name(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    updated = _account(tenant_id, name="New Name")
    mock_account_service.update_account.return_value = updated
    mock_account_service.get_account.return_value = updated

    token = _mint_token(
        tenant_id=str(tenant_id),
        roles=["admin"],
        scopes=["billing:manage"],
    )

    response = client.patch(
        "/api/v1/tenants/account",
        json={"name": "New Name"},
        headers=_headers(token=token, tenant_id=str(tenant_id), tenant_role="admin"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "New Name"
    mock_account_service.update_account.assert_awaited_once()


def test_platform_list_tenants(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id)
    mock_account_service.list_accounts.return_value = TenantAccountListResult(
        accounts=[account], total=1
    )

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.get(
        "/api/v1/platform/tenants",
        headers=_operator_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["accounts"][0]["id"] == str(tenant_id)


def test_platform_support_scope_can_list_tenants(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id)
    mock_account_service.list_accounts.return_value = TenantAccountListResult(
        accounts=[account], total=1
    )

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["support:*"],
    )

    response = client.get(
        "/api/v1/platform/tenants",
        headers=_operator_headers(token),
    )

    assert response.status_code == 200, response.text


def test_platform_create_tenant(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id)
    mock_account_service.create_account.return_value = account

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.post(
        "/api/v1/platform/tenants",
        json={"name": "Acme Corp", "slug": "acme"},
        headers=_operator_headers(token),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] == str(tenant_id)


def test_platform_get_tenant(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id)
    mock_account_service.get_account.return_value = account

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.get(
        f"/api/v1/platform/tenants/{tenant_id}",
        headers=_operator_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(tenant_id)


def test_platform_update_tenant(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id, name="Updated")
    mock_account_service.update_account.return_value = account

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.patch(
        f"/api/v1/platform/tenants/{tenant_id}",
        json={"name": "Updated"},
        headers=_operator_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Updated"


def test_operator_override_allows_read_for_suspended_tenant(
    client: TestClient, mock_account_service: AsyncMock
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id, status=TenantAccountStatus.SUSPENDED)
    mock_account_service.get_account.return_value = account

    token = _mint_token(
        tenant_id=str(tenant_id),
        roles=["owner"],
        scopes=["support:*"],
    )

    response = client.get(
        "/api/v1/tenants/account",
        headers={
            **_headers(token=token, tenant_id=str(tenant_id), tenant_role="owner"),
            **_operator_override_headers(token),
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(tenant_id)


def test_platform_suspend_tenant(
    client: TestClient,
    mock_account_service: AsyncMock,
    mock_lifecycle_service: AsyncMock,
) -> None:
    tenant_id = uuid4()
    account = _account(tenant_id, status=TenantAccountStatus.SUSPENDED)
    mock_lifecycle_service.suspend_tenant.return_value = account
    mock_account_service.get_account.return_value = account

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.post(
        f"/api/v1/platform/tenants/{tenant_id}/suspend",
        json={"reason": "policy"},
        headers=_operator_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "suspended"


def test_platform_deprovision_billing_failure(
    client: TestClient,
    mock_account_service: AsyncMock,
    mock_lifecycle_service: AsyncMock,
) -> None:
    tenant_id = uuid4()
    mock_lifecycle_service.deprovision_tenant.side_effect = TenantLifecycleBillingError(
        "billing failed"
    )
    mock_account_service.get_account.return_value = _account(tenant_id)

    token = _mint_token(
        tenant_id=None,
        roles=[],
        scopes=["platform:operator"],
    )

    response = client.post(
        f"/api/v1/platform/tenants/{tenant_id}/deprovision",
        json={"reason": "shutdown"},
        headers=_operator_headers(token),
    )

    assert response.status_code == 503
