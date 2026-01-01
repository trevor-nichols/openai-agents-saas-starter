"""Platform operator tenant management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.platform import require_platform_operator
from app.api.models.tenant_accounts import (
    TenantAccountCreateRequest,
    TenantAccountLifecycleRequest,
    TenantAccountListResponse,
    TenantAccountOperatorResponse,
    TenantAccountUpdateRequest,
)
from app.domain.tenant_accounts import TenantAccount, TenantAccountStatus
from app.observability.logging import log_event
from app.services.activity import activity_service
from app.services.tenant import (
    tenant_account_service as tenant_account_module,
)
from app.services.tenant import (
    tenant_lifecycle_service as tenant_lifecycle_module,
)
from app.services.tenant.tenant_account_service import (
    TenantAccountNotFoundError,
    TenantAccountSlugCollisionError,
    TenantAccountStatusError,
    TenantAccountValidationError,
)
from app.services.tenant.tenant_lifecycle_service import TenantLifecycleBillingError

router = APIRouter()


def _require_operator_id(user: CurrentUser) -> UUID:
    try:
        return UUID(str(user["user_id"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to resolve operator identity.",
        ) from exc


async def _record_tenant_activity(
    *,
    action: str,
    account: TenantAccount,
    actor_user_id: UUID | None,
    fields: list[str] | None = None,
    reason: str | None = None,
) -> None:
    metadata: dict[str, object] = {}
    if action == "tenant.account.created":
        metadata = {
            "slug": account.slug,
            "name": account.name,
            "status": account.status.value,
        }
        if reason:
            metadata["reason"] = reason
    elif action == "tenant.account.updated":
        metadata = {"fields": fields or []}

    try:
        await activity_service.record(
            tenant_id=str(account.id),
            action=action,
            actor_id=str(actor_user_id) if actor_user_id else None,
            actor_type="user" if actor_user_id else "system",
            actor_role="platform_operator",
            object_type="tenant",
            object_id=str(account.id),
            object_name=account.name,
            status="success",
            source="api",
            metadata=metadata,
        )
    except Exception:  # pragma: no cover - best effort
        log_event(
            "tenant.account.audit_failed",
            level="warning",
            tenant_id=str(account.id),
            action=action,
        )


@router.get("/tenants", response_model=TenantAccountListResponse)
async def list_tenants(
    status_filter: TenantAccountStatus | None = Query(default=None, alias="status"),
    query: str | None = Query(default=None, alias="q"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountListResponse:
    service = tenant_account_module.get_tenant_account_service()
    listing = await service.list_accounts(
        limit=limit,
        offset=offset,
        status=status_filter,
        query=query,
    )
    accounts = [
        TenantAccountOperatorResponse.from_domain(account)
        for account in listing.accounts
    ]
    return TenantAccountListResponse(accounts=accounts, total=listing.total)


@router.post(
    "/tenants",
    response_model=TenantAccountOperatorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant(
    payload: TenantAccountCreateRequest,
    current_user: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    service = tenant_account_module.get_tenant_account_service()
    actor_user_id = _require_operator_id(current_user)
    try:
        account = await service.create_account(
            name=payload.name,
            slug=payload.slug,
            status=TenantAccountStatus.ACTIVE,
            created_by_user_id=actor_user_id,
            reason="operator_create",
            allow_slug_suffix=payload.slug is None,
        )
    except TenantAccountValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TenantAccountSlugCollisionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    await _record_tenant_activity(
        action="tenant.account.created",
        account=account,
        actor_user_id=actor_user_id,
        reason="operator_create",
    )
    return TenantAccountOperatorResponse.from_domain(account)


@router.get("/tenants/{tenant_id}", response_model=TenantAccountOperatorResponse)
async def get_tenant(
    tenant_id: UUID,
    _: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    service = tenant_account_module.get_tenant_account_service()
    try:
        account = await service.get_account(tenant_id)
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TenantAccountOperatorResponse.from_domain(account)


@router.patch("/tenants/{tenant_id}", response_model=TenantAccountOperatorResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantAccountUpdateRequest,
    current_user: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    if payload.name is None and payload.slug is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required.",
        )
    service = tenant_account_module.get_tenant_account_service()
    actor_user_id = _require_operator_id(current_user)
    changed_fields = [
        field for field in ("name", "slug") if getattr(payload, field) is not None
    ]
    try:
        account = await service.update_account(
            tenant_id,
            name=payload.name,
            slug=payload.slug,
            allow_slug_change=True,
        )
    except TenantAccountValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TenantAccountSlugCollisionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await _record_tenant_activity(
        action="tenant.account.updated",
        account=account,
        actor_user_id=actor_user_id,
        fields=changed_fields,
    )
    return TenantAccountOperatorResponse.from_domain(account)


@router.post(
    "/tenants/{tenant_id}/suspend",
    response_model=TenantAccountOperatorResponse,
)
async def suspend_tenant(
    tenant_id: UUID,
    payload: TenantAccountLifecycleRequest,
    current_user: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    service = tenant_lifecycle_module.get_tenant_lifecycle_service()
    actor_user_id = _require_operator_id(current_user)
    try:
        account = await service.suspend_tenant(
            tenant_id,
            actor_user_id=actor_user_id,
            actor_role="platform_operator",
            reason=payload.reason,
        )
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TenantAccountStatusError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TenantAccountOperatorResponse.from_domain(account)


@router.post(
    "/tenants/{tenant_id}/reactivate",
    response_model=TenantAccountOperatorResponse,
)
async def reactivate_tenant(
    tenant_id: UUID,
    payload: TenantAccountLifecycleRequest,
    current_user: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    service = tenant_lifecycle_module.get_tenant_lifecycle_service()
    actor_user_id = _require_operator_id(current_user)
    try:
        account = await service.reactivate_tenant(
            tenant_id,
            actor_user_id=actor_user_id,
            actor_role="platform_operator",
            reason=payload.reason,
        )
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TenantAccountStatusError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TenantAccountOperatorResponse.from_domain(account)


@router.post(
    "/tenants/{tenant_id}/deprovision",
    response_model=TenantAccountOperatorResponse,
)
async def deprovision_tenant(
    tenant_id: UUID,
    payload: TenantAccountLifecycleRequest,
    current_user: CurrentUser = Depends(require_platform_operator()),
) -> TenantAccountOperatorResponse:
    service = tenant_lifecycle_module.get_tenant_lifecycle_service()
    actor_user_id = _require_operator_id(current_user)
    try:
        account = await service.deprovision_tenant(
            tenant_id,
            actor_user_id=actor_user_id,
            actor_role="platform_operator",
            reason=payload.reason,
        )
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TenantAccountStatusError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TenantLifecycleBillingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return TenantAccountOperatorResponse.from_domain(account)


__all__ = ["router"]
