"""Dependencies shared by vector store routes."""

from __future__ import annotations

from fastapi import Depends

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context


async def tenant_viewer(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
    context.ensure_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    return context


async def tenant_admin(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
    context.ensure_role(TenantRole.ADMIN, TenantRole.OWNER)
    return context


def verified_user() -> CurrentUser:
    return Depends(require_verified_user())


__all__ = ["tenant_viewer", "tenant_admin"]
