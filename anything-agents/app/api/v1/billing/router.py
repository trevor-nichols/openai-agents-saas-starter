"""Billing-related API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.tenant import (
    TenantContext,
    TenantRole,
    get_tenant_context,
    require_tenant_role,
)
from app.api.models.common import SuccessResponse
from app.api.v1.billing.schemas import (
    BillingPlanResponse,
    CancelSubscriptionRequest,
    StartSubscriptionRequest,
    TenantSubscriptionResponse,
    UpdateSubscriptionRequest,
    UsageRecordRequest,
)
from app.services.billing_service import (
    BillingError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
    InvalidTenantIdentifierError,
    billing_service,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def _assert_same_tenant(context: TenantContext, tenant_id: str) -> None:
    if context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch between request and credentials.",
        )


@router.get("/plans", response_model=list[BillingPlanResponse])
async def list_billing_plans() -> list[BillingPlanResponse]:
    """Return the catalog of available billing plans."""

    plans = await billing_service.list_plans()
    return [BillingPlanResponse.from_domain(plan) for plan in plans]


def _handle_billing_error(exc: BillingError) -> None:
    if isinstance(exc, PlanNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, SubscriptionNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, SubscriptionStateError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, InvalidTenantIdentifierError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/tenants/{tenant_id}/subscription",
    response_model=TenantSubscriptionResponse,
)
async def get_tenant_subscription(
    tenant_id: str,
    context: TenantContext = Depends(get_tenant_context),
) -> TenantSubscriptionResponse:
    """Return the current subscription for a tenant."""

    _assert_same_tenant(context, tenant_id)

    try:
        subscription = await billing_service.get_subscription(tenant_id)
    except BillingError as exc:  # pragma: no cover - translated below
        _handle_billing_error(exc)

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    return TenantSubscriptionResponse.from_domain(subscription)


@router.post(
    "/tenants/{tenant_id}/subscription",
    response_model=TenantSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_subscription(
    tenant_id: str,
    payload: StartSubscriptionRequest,
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)
    ),
) -> TenantSubscriptionResponse:
    """Provision a new subscription for the tenant."""

    _assert_same_tenant(context, tenant_id)

    try:
        subscription = await billing_service.start_subscription(
            tenant_id=tenant_id,
            plan_code=payload.plan_code,
            billing_email=payload.billing_email,
            auto_renew=payload.auto_renew,
            seat_count=payload.seat_count,
        )
    except BillingError as exc:  # pragma: no cover - translated below
        _handle_billing_error(exc)
    return TenantSubscriptionResponse.from_domain(subscription)


@router.patch(
    "/tenants/{tenant_id}/subscription",
    response_model=TenantSubscriptionResponse,
)
async def update_subscription(
    tenant_id: str,
    payload: UpdateSubscriptionRequest,
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)
    ),
) -> TenantSubscriptionResponse:
    """Adjust subscription metadata (auto-renew, seats, billing email)."""

    _assert_same_tenant(context, tenant_id)

    if (
        payload.auto_renew is None
        and payload.billing_email is None
        and payload.seat_count is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription fields provided for update.",
        )

    try:
        subscription = await billing_service.update_subscription(
            tenant_id,
            auto_renew=payload.auto_renew,
            billing_email=payload.billing_email,
            seat_count=payload.seat_count,
        )
    except BillingError as exc:  # pragma: no cover - translated below
        _handle_billing_error(exc)
    return TenantSubscriptionResponse.from_domain(subscription)


@router.post(
    "/tenants/{tenant_id}/subscription/cancel",
    response_model=TenantSubscriptionResponse,
)
async def cancel_subscription(
    tenant_id: str,
    payload: CancelSubscriptionRequest,
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)
    ),
) -> TenantSubscriptionResponse:
    """Cancel the tenant subscription (immediately or at period end)."""

    _assert_same_tenant(context, tenant_id)

    try:
        subscription = await billing_service.cancel_subscription(
            tenant_id, cancel_at_period_end=payload.cancel_at_period_end
        )
    except BillingError as exc:  # pragma: no cover - translated below
        _handle_billing_error(exc)
    return TenantSubscriptionResponse.from_domain(subscription)


@router.post(
    "/tenants/{tenant_id}/usage",
    response_model=SuccessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def record_usage(
    tenant_id: str,
    payload: UsageRecordRequest,
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)
    ),
) -> SuccessResponse:
    """Report metered usage for a tenant subscription."""

    _assert_same_tenant(context, tenant_id)

    try:
        await billing_service.record_usage(
            tenant_id,
            feature_key=payload.feature_key,
            quantity=payload.quantity,
            idempotency_key=payload.idempotency_key,
            period_start=payload.period_start,
            period_end=payload.period_end,
        )
    except BillingError as exc:  # pragma: no cover - translated below
        _handle_billing_error(exc)
    return SuccessResponse(success=True, message="Usage recorded.")
