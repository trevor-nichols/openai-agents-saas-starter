"""Billing-related API endpoints."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.tenant import (
    TenantContext,
    TenantRole,
    get_tenant_context,
    require_tenant_role,
)
from app.api.models.common import SuccessNoDataResponse
from app.api.v1.billing.schemas import (
    BillingEventHistoryResponse,
    BillingEventResponse,
    BillingPlanResponse,
    CancelSubscriptionRequest,
    StartSubscriptionRequest,
    TenantSubscriptionResponse,
    UpdateSubscriptionRequest,
    UsageRecordRequest,
)
from app.core.settings import get_settings
from app.infrastructure.persistence.stripe.models import StripeEventStatus
from app.services.billing.billing_events import get_billing_events_service
from app.services.billing.billing_service import (
    BillingError,
    InvalidTenantIdentifierError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
    billing_service,
)
from app.services.shared.rate_limit_service import (
    ConcurrencyQuota,
    RateLimitExceeded,
    RateLimitLease,
    RateLimitQuota,
    rate_limiter,
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
    context: TenantContext = Depends(require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)),
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
            trial_days=None,
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
    context: TenantContext = Depends(require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)),
) -> TenantSubscriptionResponse:
    """Adjust subscription metadata (auto-renew, seats, billing email)."""

    _assert_same_tenant(context, tenant_id)

    if payload.auto_renew is None and payload.billing_email is None and payload.seat_count is None:
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
    context: TenantContext = Depends(require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)),
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
    response_model=SuccessNoDataResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def record_usage(
    tenant_id: str,
    payload: UsageRecordRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN)),
) -> SuccessNoDataResponse:
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
    return SuccessNoDataResponse(message="Usage recorded.")


@router.get(
    "/tenants/{tenant_id}/events",
    response_model=BillingEventHistoryResponse,
)
async def list_billing_events(
    tenant_id: str,
    limit: int = Query(default=25, ge=1, le=100, description="Number of events to return."),
    cursor: str | None = Query(
        default=None, description="Opaque cursor returned from the previous page."
    ),
    event_type: str | None = Query(default=None, description="Filter by Stripe event type."),
    processing_status: StripeEventStatus | None = Query(
        default=None,
        description="Filter by processing outcome (received/processed/failed).",
    ),
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    ),
) -> BillingEventHistoryResponse:
    """Page through the tenant's historical billing events."""

    _assert_same_tenant(context, tenant_id)

    service = get_billing_events_service()
    try:
        history = await service.list_history(
            tenant_id=tenant_id,
            limit=limit,
            cursor=cursor,
            event_type=event_type,
            status=processing_status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BillingEventHistoryResponse(
        items=[BillingEventResponse.from_payload(item) for item in history.items],
        next_cursor=history.next_cursor,
    )


@router.get("/stream")
async def billing_event_stream(
    request: Request,
    context: TenantContext = Depends(
        require_tenant_role(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    ),
) -> StreamingResponse:
    settings = get_settings()
    if not settings.enable_billing_stream:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Billing stream is disabled."
        )

    service = get_billing_events_service()
    await _enforce_tenant_quota(
        quota=RateLimitQuota(
            name="billing_stream_per_minute",
            limit=settings.billing_stream_rate_limit_per_minute,
            window_seconds=60,
            scope="tenant",
        ),
        context=context,
    )
    stream_lease = await _acquire_tenant_stream_slot(
        quota=ConcurrencyQuota(
            name="billing_stream_concurrency",
            limit=settings.billing_stream_concurrent_limit,
            ttl_seconds=300,
            scope="tenant",
        ),
        context=context,
    )

    async def event_generator() -> AsyncIterator[str]:
        async with stream_lease:
            subscription = await service.subscribe(context.tenant_id)
            keepalive_interval = 15.0
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(
                            subscription.next_message(timeout=keepalive_interval),
                            timeout=keepalive_interval + 1,
                        )
                    except TimeoutError:
                        if await request.is_disconnected():
                            break
                        yield ": ping\n\n"
                        continue
                    if message is None:
                        if await request.is_disconnected():
                            break
                        yield ": ping\n\n"
                        continue
                    if await request.is_disconnected():
                        break
                    yield f"data: {message}\n\n"
            finally:
                await subscription.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _enforce_tenant_quota(quota: RateLimitQuota, context: TenantContext) -> None:
    if quota.limit <= 0:
        return
    tenant_id = context.tenant_id
    try:
        await rate_limiter.enforce(quota, [tenant_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=context.user.get("user_id"))


async def _acquire_tenant_stream_slot(
    quota: ConcurrencyQuota,
    context: TenantContext,
) -> RateLimitLease:
    if quota.limit <= 0:
        return RateLimitLease(None, None)
    tenant_id = context.tenant_id
    try:
        return await rate_limiter.acquire_concurrency(quota, [tenant_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=context.user.get("user_id"))
