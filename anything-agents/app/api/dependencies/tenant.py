"""Tenant context helpers for multi-tenant aware endpoints."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import Enum
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.api.dependencies.auth import CurrentUser, require_current_user


class TenantRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


_ROLE_PRIORITY: dict[TenantRole, int] = {
    TenantRole.VIEWER: 1,
    TenantRole.ADMIN: 2,
    TenantRole.OWNER: 3,
}


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
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    current_user: CurrentUser = Depends(require_current_user),
) -> TenantContext:
    """Resolve tenant context using JWT claims (headers may only down-scope access)."""

    header_tenant = tenant_id_header if isinstance(tenant_id_header, str) else None
    header_role = tenant_role_header if isinstance(tenant_role_header, str) else None

    payload = current_user.get("payload", {})
    token_tenant = payload.get("tenant_id")
    effective_tenant = token_tenant

    if effective_tenant:
        if header_tenant and header_tenant != effective_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch between token and X-Tenant-Id header.",
            )
    else:
        if not header_tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated token is missing tenant context.",
            )
        effective_tenant = header_tenant

    if not effective_tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated token is missing tenant context.",
        )

    granted_role = _role_from_claims(payload)
    requested_role = _normalize_role(header_role)
    role = _select_effective_role(granted_role, requested_role)

    return TenantContext(tenant_id=effective_tenant, role=role, user=current_user)


def require_tenant_role(*allowed: TenantRole):
    """Dependency factory enforcing that the caller has one of the allowed roles."""

    async def _dependency(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        context.ensure_role(*allowed)
        return context

    return _dependency


def _role_from_claims(payload: dict[str, Any]) -> TenantRole:
    role: TenantRole | None = None

    roles_claim = payload.get("roles")
    role = _max_role(role, _role_from_roles(roles_claim))

    scope_claim = payload.get("scope")
    role = _max_role(role, _role_from_scopes(scope_claim))

    return role or TenantRole.VIEWER


def _role_from_roles(roles_claim: Any) -> TenantRole | None:
    if roles_claim is None:
        return None
    if isinstance(roles_claim, str):
        return _normalize_role(roles_claim)
    if isinstance(roles_claim, Sequence):
        resolved: TenantRole | None = None
        for value in roles_claim:
            resolved = _max_role(resolved, _normalize_role(value))
        return resolved
    return None


def _role_from_scopes(scope_claim: Any) -> TenantRole | None:
    scopes: Iterable[str] = []
    if isinstance(scope_claim, str):
        scopes = scope_claim.split()
    elif isinstance(scope_claim, Sequence):
        scopes = [str(item) for item in scope_claim]

    resolved: TenantRole | None = None
    for scope in scopes:
        normalized = scope.lower().strip()
        if normalized == "billing:manage":
            resolved = _max_role(resolved, TenantRole.OWNER)
        elif normalized == "billing:read":
            resolved = _max_role(resolved, TenantRole.VIEWER)
    return resolved


def _select_effective_role(
    granted: TenantRole | None,
    requested: TenantRole | None,
) -> TenantRole:
    effective = granted or TenantRole.VIEWER
    if requested is None:
        return effective

    if _ROLE_PRIORITY[requested] > _ROLE_PRIORITY[effective]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requested tenant role exceeds privileges granted by token.",
        )
    return requested


def _normalize_role(value: Any) -> TenantRole | None:
    if value is None:
        return None
    try:
        return TenantRole(str(value).lower())
    except ValueError:
        return None


def _max_role(current: TenantRole | None, candidate: TenantRole | None) -> TenantRole | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    if _ROLE_PRIORITY[candidate] > _ROLE_PRIORITY[current]:
        return candidate
    return current
