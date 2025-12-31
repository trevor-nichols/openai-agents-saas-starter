"""Dependencies for service-account administration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fastapi import Depends, Header, HTTPException, Request, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.platform import has_operator_scope
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context
from app.services.tenant.tenant_account_service import get_tenant_account_service


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
    request: Request,
    tenant_id_header: str | None = Header(default=None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(default=None, alias="X-Tenant-Role"),
    current_user: CurrentUser = Depends(require_verified_user()),
) -> TenantContext | None:
    try:
        context = await get_tenant_context(
            request=request,
            tenant_id_header=tenant_id_header,
            tenant_role_header=tenant_role_header,
            current_user=current_user,
            tenant_account_service=get_tenant_account_service(),
        )
    except HTTPException:
        return None
    try:
        context.ensure_role(TenantRole.ADMIN, TenantRole.OWNER)
    except HTTPException:
        return None
    return context


async def require_service_account_actor(
    tenant_context: TenantContext | None = Depends(_optional_tenant_admin_context),
    current_user: CurrentUser = Depends(require_verified_user()),
) -> ServiceAccountActor:
    if tenant_context is not None:
        return ServiceAccountActor(
            actor_type=ServiceAccountActorType.TENANT_ADMIN,
            tenant_id=tenant_context.tenant_id,
            user=current_user,
        )

    if has_operator_scope(current_user):
        return ServiceAccountActor(
            actor_type=ServiceAccountActorType.PLATFORM_OPERATOR,
            tenant_id=None,
            user=current_user,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Tenant admin privileges or operator scope required for service-account actions."
        ),
    )


__all__ = [
    "ServiceAccountActor",
    "ServiceAccountActorType",
    "require_service_account_actor",
]
