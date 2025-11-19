"""Tenant settings endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.tenant_settings import TenantSettingsResponse, TenantSettingsUpdateRequest
from app.services.tenant.tenant_settings_service import (
    TenantSettingsValidationError,
    tenant_settings_service,
)

router = APIRouter()


@router.get("/settings", response_model=TenantSettingsResponse)
async def get_tenant_settings(
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
) -> TenantSettingsResponse:
    snapshot = await tenant_settings_service.get_settings(context.tenant_id)
    return TenantSettingsResponse.from_snapshot(snapshot)


@router.put("/settings", response_model=TenantSettingsResponse)
async def update_tenant_settings(
    payload: TenantSettingsUpdateRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
) -> TenantSettingsResponse:
    mapped = payload.dict_for_service()
    try:
        snapshot = await tenant_settings_service.update_settings(
            context.tenant_id,
            billing_contacts=mapped["billing_contacts"],
            billing_webhook_url=mapped["billing_webhook_url"],
            plan_metadata=mapped["plan_metadata"],
            flags=mapped["flags"],
        )
    except TenantSettingsValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TenantSettingsResponse.from_snapshot(snapshot)
