"""Pydantic schemas for billing endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.domain.billing import (
    BillingPlan,
    PlanFeature,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.services.billing.billing_events import (
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventSubscription,
    BillingEventUsage,
)
from app.services.billing.models import (
    PlanChangeResult,
    PlanChangeTiming,
    UpcomingInvoicePreview,
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
    pending_plan_code: str | None = None
    pending_plan_effective_at: datetime | None = None
    pending_seat_count: int | None = None
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
            pending_plan_code=subscription.pending_plan_code,
            pending_plan_effective_at=subscription.pending_plan_effective_at,
            pending_seat_count=subscription.pending_seat_count,
            metadata=subscription.metadata,
        )


class SubscriptionInvoiceResponse(BaseModel):
    invoice_id: str | None = None
    status: str
    amount_cents: int
    currency: str
    period_start: datetime
    period_end: datetime
    hosted_invoice_url: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_domain(
        cls, invoice: SubscriptionInvoiceRecord
    ) -> SubscriptionInvoiceResponse:
        return cls(
            invoice_id=invoice.processor_invoice_id,
            status=invoice.status,
            amount_cents=invoice.amount_cents,
            currency=invoice.currency,
            period_start=invoice.period_start,
            period_end=invoice.period_end,
            hosted_invoice_url=invoice.hosted_invoice_url,
            created_at=invoice.created_at,
        )


class SubscriptionInvoiceListResponse(BaseModel):
    items: list[SubscriptionInvoiceResponse] = Field(default_factory=list)
    next_offset: int | None = None


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


class ChangeSubscriptionPlanRequest(BaseModel):
    plan_code: str = Field(..., description="Billing plan to activate.")
    seat_count: PositiveSeatCount | None = Field(
        default=None,
        description="Optional seat count override for the new plan.",
    )
    timing: PlanChangeTiming = Field(
        default=PlanChangeTiming.AUTO,
        description=(
            "When the plan change takes effect (auto selects immediate for upgrades and "
            "period-end for downgrades when intervals match)."
        ),
    )


class PlanChangeResponse(BaseModel):
    subscription: TenantSubscriptionResponse
    target_plan_code: str
    effective_at: datetime | None = None
    seat_count: int | None = None
    timing: PlanChangeTiming = PlanChangeTiming.AUTO

    @classmethod
    def from_result(cls, result: PlanChangeResult) -> PlanChangeResponse:
        return cls(
            subscription=TenantSubscriptionResponse.from_domain(result.subscription),
            target_plan_code=result.target_plan_code,
            effective_at=result.effective_at,
            seat_count=result.seat_count,
            timing=result.timing,
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


class UsageTotalResponse(BaseModel):
    feature_key: str
    unit: str
    quantity: int
    window_start: datetime
    window_end: datetime

    @classmethod
    def from_domain(cls, total: UsageTotal) -> UsageTotalResponse:
        return cls(
            feature_key=total.feature_key,
            unit=total.unit,
            quantity=total.quantity,
            window_start=total.window_start,
            window_end=total.window_end,
        )


class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = Field(
        default=True,
        description="If true, cancellation occurs at the current period end.",
    )


class PortalSessionRequest(BaseModel):
    billing_email: EmailStr | None = Field(
        default=None, description="Optional billing email to associate with the customer."
    )


class PortalSessionResponse(BaseModel):
    url: str


class PaymentMethodResponse(BaseModel):
    id: str
    brand: str | None = None
    last4: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None
    is_default: bool = False


class SetupIntentRequest(BaseModel):
    billing_email: EmailStr | None = Field(
        default=None, description="Optional billing email to associate with the customer."
    )


class SetupIntentResponse(BaseModel):
    id: str
    client_secret: str | None = None


class UpcomingInvoicePreviewRequest(BaseModel):
    seat_count: PositiveSeatCount | None = Field(
        default=None, description="Optional seat count override for previewing charges."
    )


class UpcomingInvoiceLineResponse(BaseModel):
    description: str | None = None
    amount_cents: int
    currency: str | None = None
    quantity: int | None = None
    unit_amount_cents: int | None = None
    price_id: str | None = None


class UpcomingInvoicePreviewResponse(BaseModel):
    plan_code: str
    plan_name: str
    seat_count: int | None = None
    invoice_id: str | None = None
    amount_due_cents: int
    currency: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    lines: list[UpcomingInvoiceLineResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, preview: UpcomingInvoicePreview) -> UpcomingInvoicePreviewResponse:
        return cls(
            plan_code=preview.plan_code,
            plan_name=preview.plan_name,
            seat_count=preview.seat_count,
            invoice_id=preview.invoice_id,
            amount_due_cents=preview.amount_due_cents,
            currency=preview.currency,
            period_start=preview.period_start,
            period_end=preview.period_end,
            lines=[
                UpcomingInvoiceLineResponse(
                    description=line.description,
                    amount_cents=line.amount_cents,
                    currency=line.currency,
                    quantity=line.quantity,
                    unit_amount_cents=line.unit_amount_cents,
                    price_id=line.price_id,
                )
                for line in preview.lines
            ],
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
