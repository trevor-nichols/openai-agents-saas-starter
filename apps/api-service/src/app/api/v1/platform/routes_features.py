"""Platform operator feature entitlement endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.platform import require_platform_operator
from app.api.models.features import (
    TenantFeatureEntitlementsResponse,
    TenantFeatureEntitlementsUpdateRequest,
)
from app.services.feature_flags import (
    FeatureEntitlementService,
    get_feature_entitlement_service,
)
from app.services.tenant.tenant_account_service import (
    TenantAccountNotFoundError,
    TenantAccountService,
    get_tenant_account_service,
)

router = APIRouter()


async def _require_tenant_exists(
    tenant_id: UUID,
    tenant_account_service: TenantAccountService = Depends(get_tenant_account_service),
) -> None:
    try:
        await tenant_account_service.get_account(tenant_id)
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/tenants/{tenant_id}/features",
    response_model=TenantFeatureEntitlementsResponse,
)
async def get_tenant_feature_entitlements(
    tenant_id: UUID,
    _: CurrentUser = Depends(require_platform_operator()),
    _tenant_check: None = Depends(_require_tenant_exists),
    service: FeatureEntitlementService = Depends(get_feature_entitlement_service),
) -> TenantFeatureEntitlementsResponse:
    snapshot = await service.get_entitlements(str(tenant_id))
    return TenantFeatureEntitlementsResponse.from_snapshot(snapshot)


@router.put(
    "/tenants/{tenant_id}/features",
    response_model=TenantFeatureEntitlementsResponse,
)
async def update_tenant_feature_entitlements(
    tenant_id: UUID,
    payload: TenantFeatureEntitlementsUpdateRequest,
    _: CurrentUser = Depends(require_platform_operator()),
    _tenant_check: None = Depends(_require_tenant_exists),
    service: FeatureEntitlementService = Depends(get_feature_entitlement_service),
) -> TenantFeatureEntitlementsResponse:
    snapshot = await service.update_entitlements(
        str(tenant_id), updates=payload.dict_for_service()
    )
    return TenantFeatureEntitlementsResponse.from_snapshot(snapshot)


__all__ = ["router"]
