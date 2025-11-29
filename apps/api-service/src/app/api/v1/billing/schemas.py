"""Pydantic schemas for billing endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.domain.billing import BillingPlan, PlanFeature, TenantSubscription
from app.services.billing.billing_events import (
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventSubscription,
    BillingEventUsage,
)

PositiveSeatCount = Annotated[int, Field(gt=0)]
PositiveUsageQuantity = Annotated[int, Field(gt=0)]


class PlanFeatureResponse(BaseModel):
    key: str
    display_name: str
    description: str | None = None
    hard_limit: int | None = None
    soft_limit: int | None = None
    is_metered: bool = False

    @classmethod
    def from_domain(cls, feature: PlanFeature) -> PlanFeatureResponse:
        return cls(
            key=feature.key,
            display_name=feature.display_name,
            description=feature.description,
            hard_limit=feature.hard_limit,
            soft_limit=feature.soft_limit,
            is_metered=feature.is_metered,
        )


class BillingPlanResponse(BaseModel):
    code: str
    name: str
    interval: str
    interval_count: int
    price_cents: int
    currency: str
    trial_days: int | None = None
    seat_included: int | None = None
    feature_toggles: dict[str, bool] = Field(default_factory=dict)
    is_active: bool = True
    features: list[PlanFeatureResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, plan: BillingPlan) -> BillingPlanResponse:
        return cls(
            code=plan.code,
            name=plan.name,
            interval=plan.interval,
            interval_count=plan.interval_count,
            price_cents=plan.price_cents,
            currency=plan.currency,
            trial_days=plan.trial_days,
            seat_included=plan.seat_included,
            feature_toggles=plan.feature_toggles,
            is_active=plan.is_active,
            features=[PlanFeatureResponse.from_domain(feature) for feature in plan.features],
        )


class TenantSubscriptionResponse(BaseModel):
    tenant_id: str
    plan_code: str
    status: str
    auto_renew: bool
    billing_email: str | None
    starts_at: datetime
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    trial_ends_at: datetime | None = None
    cancel_at: datetime | None = None
    seat_count: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_domain(cls, subscription: TenantSubscription) -> TenantSubscriptionResponse:
        return cls(
            tenant_id=subscription.tenant_id,
            plan_code=subscription.plan_code,
            status=subscription.status,
            auto_renew=subscription.auto_renew,
            billing_email=subscription.billing_email,
            starts_at=subscription.starts_at,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_ends_at=subscription.trial_ends_at,
            cancel_at=subscription.cancel_at,
            seat_count=subscription.seat_count,
            metadata=subscription.metadata,
        )


class StartSubscriptionRequest(BaseModel):
    plan_code: str = Field(..., description="Billing plan to activate.")
    billing_email: EmailStr | None = Field(default=None, description="Primary billing contact.")
    auto_renew: bool = Field(default=True, description="Whether the subscription auto-renews.")
    seat_count: PositiveSeatCount | None = Field(
        default=None, description="Optional explicit seat count override."
    )


class UpdateSubscriptionRequest(BaseModel):
    auto_renew: bool | None = Field(default=None, description="Toggle auto-renewal.")
    billing_email: EmailStr | None = Field(default=None, description="Override billing contact.")
    seat_count: PositiveSeatCount | None = Field(
        default=None, description="Adjust allocated seats."
    )


class UsageRecordRequest(BaseModel):
    feature_key: str = Field(..., description="Identifier of the metered feature.")
    quantity: PositiveUsageQuantity = Field(
        ..., description="Units consumed in this report."
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Client-provided key to deduplicate usage submissions.",
    )
    period_start: datetime | None = Field(default=None, description="Billing period start (UTC).")
    period_end: datetime | None = Field(default=None, description="Billing period end (UTC).")


class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = Field(
        default=True,
        description="If true, cancellation occurs at the current period end.",
    )


class BillingEventSubscriptionResponse(BaseModel):
    plan_code: str
    status: str
    seat_count: int | None = None
    auto_renew: bool
    current_period_start: str | None = None
    current_period_end: str | None = None
    trial_ends_at: str | None = None
    cancel_at: str | None = None

    @classmethod
    def from_payload(cls, payload: BillingEventSubscription) -> BillingEventSubscriptionResponse:
        return cls(
            plan_code=payload.plan_code,
            status=payload.status,
            seat_count=payload.seat_count,
            auto_renew=payload.auto_renew,
            current_period_start=payload.current_period_start,
            current_period_end=payload.current_period_end,
            trial_ends_at=payload.trial_ends_at,
            cancel_at=payload.cancel_at,
        )


class BillingEventInvoiceResponse(BaseModel):
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    billing_reason: str | None = None
    hosted_invoice_url: str | None = None
    collection_method: str | None = None
    period_start: str | None = None
    period_end: str | None = None

    @classmethod
    def from_payload(cls, payload: BillingEventInvoice) -> BillingEventInvoiceResponse:
        return cls(
            invoice_id=payload.invoice_id,
            status=payload.status,
            amount_due_cents=payload.amount_due_cents,
            currency=payload.currency,
            billing_reason=payload.billing_reason,
            hosted_invoice_url=payload.hosted_invoice_url,
            collection_method=payload.collection_method,
            period_start=payload.period_start,
            period_end=payload.period_end,
        )


class BillingEventUsageResponse(BaseModel):
    feature_key: str
    quantity: int
    period_start: str | None = None
    period_end: str | None = None
    amount_cents: int | None = None

    @classmethod
    def from_payload(cls, payload: BillingEventUsage) -> BillingEventUsageResponse:
        return cls(
            feature_key=payload.feature_key,
            quantity=payload.quantity,
            period_start=payload.period_start,
            period_end=payload.period_end,
            amount_cents=payload.amount_cents,
        )


class BillingEventResponse(BaseModel):
    tenant_id: str
    event_type: str
    stripe_event_id: str
    occurred_at: str
    summary: str | None = None
    status: str
    subscription: BillingEventSubscriptionResponse | None = None
    invoice: BillingEventInvoiceResponse | None = None
    usage: list[BillingEventUsageResponse] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: BillingEventPayload) -> BillingEventResponse:
        return cls(
            tenant_id=payload.tenant_id,
            event_type=payload.event_type,
            stripe_event_id=payload.stripe_event_id,
            occurred_at=payload.occurred_at,
            summary=payload.summary,
            status=payload.status,
            subscription=(
                BillingEventSubscriptionResponse.from_payload(payload.subscription)
                if payload.subscription
                else None
            ),
            invoice=(
                BillingEventInvoiceResponse.from_payload(payload.invoice)
                if payload.invoice
                else None
            ),
            usage=[BillingEventUsageResponse.from_payload(entry) for entry in payload.usage],
        )


class BillingEventHistoryResponse(BaseModel):
    items: list[BillingEventResponse] = Field(default_factory=list)
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the next page. Null when no additional events exist.",
    )
