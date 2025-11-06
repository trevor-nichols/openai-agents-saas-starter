"""Tenant context helpers for multi-tenant aware endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.api.dependencies.auth import require_current_user


class TenantRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class TenantContext:
    """Lightweight representation of the active tenant request scope."""

    def __init__(
        self,
        tenant_id: str,
        role: TenantRole,
        user: dict[str, Any],
    ) -> None:
        self.tenant_id = tenant_id
        self.role = role
        self.user = user

    def ensure_role(self, *allowed: TenantRole) -> None:
        if self.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient tenant privileges for this operation.",
            )


async def get_tenant_context(
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role: str | None = Header("viewer", alias="X-Tenant-Role"),
    current_user: dict[str, Any] = Depends(require_current_user),
) -> TenantContext:
    """Resolve tenant context from headers (temporary until full auth lands)."""

    if tenant_id_header is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Tenant-Id header.",
        )

    try:
        role = TenantRole(tenant_role.lower() if tenant_role else "viewer")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported tenant role '{tenant_role}'.",
        ) from exc

    return TenantContext(tenant_id=tenant_id_header, role=role, user=current_user)


def require_tenant_role(*allowed: TenantRole):
    """Dependency factory enforcing that the caller has one of the allowed roles."""

    async def _dependency(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        context.ensure_role(*allowed)
        return context

    return _dependency
