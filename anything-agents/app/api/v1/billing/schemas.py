"""Pydantic schemas for billing endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.domain.billing import BillingPlan, PlanFeature, TenantSubscription

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
