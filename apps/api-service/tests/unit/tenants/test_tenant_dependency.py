"""Unit tests for tenant context derivation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.dependencies.tenant import TenantRole, get_tenant_context
from app.domain.tenant_accounts import TenantAccountStatus
from app.services.tenant.tenant_account_service import TenantAccountService
from tests.utils.tenant_accounts import StubTenantAccountRepository


def _request(method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
    }
    return Request(scope)


def _tenant_service(status: TenantAccountStatus = TenantAccountStatus.ACTIVE) -> TenantAccountService:
    return TenantAccountService(
        repository=StubTenantAccountRepository(default_status=status),
    )


@pytest.mark.asyncio
async def test_context_uses_token_claims() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scope": "billing:manage billing:read",
        }
    }
    context = await get_tenant_context(
        current_user=user,
        request=_request(),
        tenant_account_service=_tenant_service(),
    )
    assert context.tenant_id == tenant_id
    # billing:manage does not elevate beyond admin for tenant-scoped roles
    assert context.role == TenantRole.ADMIN


@pytest.mark.asyncio
async def test_roles_claim_preferred_over_scopes() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["viewer"],
            "scope": "billing:manage",
        }
    }
    context = await get_tenant_context(
        current_user=user,
        request=_request(),
        tenant_account_service=_tenant_service(),
    )
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_billing_read_scope_maps_to_viewer() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "scope": "billing:read",
        }
    }
    context = await get_tenant_context(
        current_user=user,
        request=_request(),
        tenant_account_service=_tenant_service(),
    )
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_missing_tenant_claim_requires_header() -> None:
    user: dict[str, object] = {"payload": {}}
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            current_user=user,
            request=_request(),
            tenant_account_service=_tenant_service(),
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_header_supplies_tenant_when_claim_missing() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {"payload": {"scope": "support:*"}}
    context = await get_tenant_context(
        tenant_id_header=tenant_id,
        current_user=user,
        request=_request(),
        tenant_account_service=_tenant_service(),
    )
    assert context.tenant_id == tenant_id
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_header_mismatch_is_forbidden() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {"payload": {"tenant_id": tenant_id}}
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            tenant_id_header=str(uuid4()),
            current_user=user,
            request=_request(),
            tenant_account_service=_tenant_service(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_header_may_downscope_role() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["owner"],
        }
    }
    context = await get_tenant_context(
        tenant_role_header="viewer",
        current_user=user,
        request=_request(),
        tenant_account_service=_tenant_service(),
    )
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_header_cannot_escalate_role() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["viewer"],
            "scope": "billing:read",
        }
    }
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            tenant_role_header="owner",
            current_user=user,
            request=_request(),
            tenant_account_service=_tenant_service(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_suspended_tenant_rejected() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scope": "billing:manage",
        }
    }
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            current_user=user,
            request=_request(),
            tenant_account_service=_tenant_service(TenantAccountStatus.SUSPENDED),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_provisioning_tenant_rejected() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scope": "billing:manage",
        }
    }
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            current_user=user,
            request=_request(),
            tenant_account_service=_tenant_service(TenantAccountStatus.PROVISIONING),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_operator_override_allows_read_only_for_suspended() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "user_id": str(uuid4()),
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scope": "support:*",
        },
    }
    context = await get_tenant_context(
        current_user=user,
        operator_override_header="true",
        operator_reason_header="investigation",
        request=_request(method="GET"),
        tenant_account_service=_tenant_service(TenantAccountStatus.SUSPENDED),
    )
    assert context.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_operator_override_rejects_write_for_suspended() -> None:
    tenant_id = str(uuid4())
    user: dict[str, object] = {
        "user_id": str(uuid4()),
        "payload": {
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scope": "support:*",
        },
    }
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            current_user=user,
            operator_override_header="true",
            operator_reason_header="investigation",
            request=_request(method="POST"),
            tenant_account_service=_tenant_service(TenantAccountStatus.SUSPENDED),
        )
    assert exc.value.status_code == 403
