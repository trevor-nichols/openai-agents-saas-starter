"""Unit tests for tenant context derivation."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.dependencies.tenant import TenantRole, get_tenant_context


@pytest.mark.asyncio
async def test_context_uses_token_claims() -> None:
    user: dict[str, object] = {
        "payload": {
            "tenant_id": "tenant-123",
            "roles": ["admin"],
            "scope": "billing:manage billing:read",
        }
    }
    context = await get_tenant_context(current_user=user)
    assert context.tenant_id == "tenant-123"
    # billing:manage does not elevate beyond admin for tenant-scoped roles
    assert context.role == TenantRole.ADMIN


@pytest.mark.asyncio
async def test_billing_read_scope_maps_to_viewer() -> None:
    user: dict[str, object] = {
        "payload": {
            "tenant_id": "tenant-123",
            "scope": "billing:read",
        }
    }
    context = await get_tenant_context(current_user=user)
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_missing_tenant_claim_requires_header() -> None:
    user: dict[str, object] = {"payload": {}}
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(current_user=user)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_header_supplies_tenant_when_claim_missing() -> None:
    user: dict[str, object] = {"payload": {"scope": "support:*"}}
    context = await get_tenant_context(
        tenant_id_header="tenant-global",
        current_user=user,
    )
    assert context.tenant_id == "tenant-global"
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_header_mismatch_is_forbidden() -> None:
    user: dict[str, object] = {"payload": {"tenant_id": "tenant-abc"}}
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(tenant_id_header="tenant-other", current_user=user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_header_may_downscope_role() -> None:
    user: dict[str, object] = {
        "payload": {
            "tenant_id": "tenant-123",
            "roles": ["owner"],
        }
    }
    context = await get_tenant_context(
        tenant_role_header="viewer",
        current_user=user,
    )
    assert context.role == TenantRole.VIEWER


@pytest.mark.asyncio
async def test_header_cannot_escalate_role() -> None:
    user: dict[str, object] = {
        "payload": {
            "tenant_id": "tenant-123",
            "roles": ["viewer"],
            "scope": "billing:read",
        }
    }
    with pytest.raises(HTTPException) as exc:
        await get_tenant_context(
            tenant_role_header="owner",
            current_user=user,
        )
    assert exc.value.status_code == 403
