"""Dependencies for service-account administration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.api.dependencies.auth import CurrentUser, require_current_user, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context


class ServiceAccountActorType(str, Enum):
    TENANT_ADMIN = "tenant_admin"
    PLATFORM_OPERATOR = "platform_operator"


@dataclass(slots=True)
class ServiceAccountActor:
    actor_type: ServiceAccountActorType
    tenant_id: str | None
    user: CurrentUser
    reason: str | None = None


async def _optional_tenant_admin_context(
    tenant_id_header: str | None = Header(default=None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(default=None, alias="X-Tenant-Role"),
    current_user: CurrentUser = Depends(require_verified_user()),
) -> TenantContext | None:
    try:
        context = await get_tenant_context(tenant_id_header, tenant_role_header, current_user)
    except HTTPException:
        return None
    try:
        context.ensure_role(TenantRole.ADMIN, TenantRole.OWNER)
    except HTTPException:
        return None
    return context


async def require_service_account_actor(
    operator_override: str | None = Header(default=None, alias="X-Operator-Override"),
    operator_reason: str | None = Header(default=None, alias="X-Operator-Reason"),
    tenant_context: TenantContext | None = Depends(_optional_tenant_admin_context),
    current_user: CurrentUser = Depends(require_current_user),
) -> ServiceAccountActor:
    if _is_truthy(operator_override):
        return _resolve_operator_actor(current_user, operator_reason)

    if tenant_context is not None:
        return ServiceAccountActor(
            actor_type=ServiceAccountActorType.TENANT_ADMIN,
            tenant_id=tenant_context.tenant_id,
            user=current_user,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Tenant admin privileges required or set X-Operator-Override header "
            "to act as operator."
        ),
    )


def _resolve_operator_actor(user: CurrentUser, reason: str | None) -> ServiceAccountActor:
    if not _has_operator_scope(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform operator scope (support:*) required for override.",
        )
    if not reason or not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Operator-Reason header is required when X-Operator-Override is true.",
        )
    return ServiceAccountActor(
        actor_type=ServiceAccountActorType.PLATFORM_OPERATOR,
        tenant_id=None,
        user=user,
        reason=reason.strip(),
    )


def _has_operator_scope(user: CurrentUser) -> bool:
    payload = user.get("payload") if isinstance(user, dict) else None
    if not isinstance(payload, dict):
        return False
    scopes: set[str] = set()
    _consume_scope_claim(payload.get("scope"), scopes)
    _consume_scope_claim(payload.get("scopes"), scopes)
    return any(scope in scopes for scope in ("support:*", "platform:operator"))


def _consume_scope_claim(value: Any, scopes: set[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        scopes.update(item.strip() for item in value.split() if item.strip())
    elif isinstance(value, list | tuple | set):
        for item in value:
            if isinstance(item, str) and item.strip():
                scopes.add(item.strip())


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


__all__ = [
    "ServiceAccountActor",
    "ServiceAccountActorType",
    "require_service_account_actor",
]
