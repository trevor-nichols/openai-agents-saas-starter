"""Tenant account self-service endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.tenant_accounts import (
    TenantAccountResponse,
    TenantAccountSelfUpdateRequest,
)
from app.services.tenant import tenant_account_service as tenant_account_module
from app.services.tenant.tenant_account_service import (
    TenantAccountNotFoundError,
    TenantAccountValidationError,
)

router = APIRouter()


def _tenant_uuid(context: TenantContext) -> UUID:
    try:
        return UUID(context.tenant_id)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context must be a valid UUID.",
        ) from exc


@router.get("/account", response_model=TenantAccountResponse)
async def get_tenant_account(
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
) -> TenantAccountResponse:
    service = tenant_account_module.get_tenant_account_service()
    try:
        account = await service.get_account(_tenant_uuid(context))
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TenantAccountResponse.from_domain(account)


@router.patch("/account", response_model=TenantAccountResponse)
async def update_tenant_account(
    payload: TenantAccountSelfUpdateRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
) -> TenantAccountResponse:
    service = tenant_account_module.get_tenant_account_service()
    try:
        account = await service.update_account(
            _tenant_uuid(context),
            name=payload.name,
            allow_slug_change=False,
        )
    except TenantAccountValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TenantAccountResponse.from_domain(account)


__all__ = ["router"]
