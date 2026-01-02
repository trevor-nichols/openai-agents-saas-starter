"""ORM-to-domain mapping helpers for billing persistence."""

from __future__ import annotations

from app.domain.billing import (
    BillingCustomerRecord,
    BillingPlan,
    PlanFeature,
    SubscriptionInvoiceRecord,
    TenantSubscription,
)
from app.infrastructure.persistence.billing.metadata import (
    coerce_int,
    parse_metadata_datetime,
)
from app.infrastructure.persistence.billing.models import (
    BillingCustomer as ORMBillingCustomer,
)
from app.infrastructure.persistence.billing.models import (
    BillingPlan as ORMPlan,
)
from app.infrastructure.persistence.billing.models import (
    PlanFeature as ORMPlanFeature,
)
from app.infrastructure.persistence.billing.models import (
    SubscriptionInvoice as ORMSubscriptionInvoice,
)
from app.infrastructure.persistence.billing.models import (
    TenantSubscription as ORMTenantSubscription,
)


def to_domain_plan(plan: ORMPlan) -> BillingPlan:
    return BillingPlan(
        code=plan.code,
        name=plan.name,
        interval=plan.interval,
        interval_count=plan.interval_count,
        price_cents=plan.price_cents,
        currency=plan.currency,
        trial_days=plan.trial_days,
        seat_included=plan.seat_included,
        feature_toggles=plan.feature_toggles or {},
        features=[to_domain_feature(feature) for feature in plan.features],
        is_active=plan.is_active,
    )


def to_domain_feature(feature: ORMPlanFeature) -> PlanFeature:
    return PlanFeature(
        key=feature.feature_key,
        display_name=feature.display_name or feature.feature_key,
        description=feature.description,
        hard_limit=feature.hard_limit,
        soft_limit=feature.soft_limit,
        is_metered=feature.is_metered,
    )


def to_domain_subscription(subscription: ORMTenantSubscription) -> TenantSubscription:
    metadata_payload = dict(subscription.metadata_json or {})
    pending_plan_code = metadata_payload.pop("pending_plan_code", None)
    if pending_plan_code == "":
        pending_plan_code = None
    pending_plan_effective_at = parse_metadata_datetime(
        metadata_payload.pop("pending_plan_effective_at", None)
    )
    pending_seat_count = metadata_payload.pop("pending_seat_count", None)
    processor_schedule_id = metadata_payload.pop("processor_schedule_id", None)
    if processor_schedule_id == "":
        processor_schedule_id = None

    return TenantSubscription(
        tenant_id=str(subscription.tenant_id),
        plan_code=_safe_plan_code(subscription),
        status=subscription.status,
        auto_renew=subscription.auto_renew,
        billing_email=subscription.billing_email,
        starts_at=subscription.starts_at,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_ends_at=subscription.trial_ends_at,
        cancel_at=subscription.cancel_at,
        seat_count=subscription.seat_count,
        pending_plan_code=pending_plan_code,
        pending_plan_effective_at=pending_plan_effective_at,
        pending_seat_count=coerce_int(pending_seat_count),
        metadata=metadata_payload,
        processor=subscription.processor,
        processor_customer_id=subscription.processor_customer_id,
        processor_subscription_id=subscription.processor_subscription_id,
        processor_schedule_id=processor_schedule_id,
    )


def to_domain_customer(customer: ORMBillingCustomer) -> BillingCustomerRecord:
    return BillingCustomerRecord(
        tenant_id=str(customer.tenant_id),
        processor=customer.processor,
        processor_customer_id=customer.processor_customer_id,
        billing_email=customer.billing_email,
    )


def to_domain_invoice(
    invoice: ORMSubscriptionInvoice, *, tenant_id: str
) -> SubscriptionInvoiceRecord:
    return SubscriptionInvoiceRecord(
        tenant_id=tenant_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        amount_cents=invoice.amount_cents,
        currency=invoice.currency,
        status=invoice.status,
        processor_invoice_id=invoice.external_invoice_id,
        hosted_invoice_url=invoice.hosted_invoice_url,
        created_at=invoice.created_at,
    )


def _safe_plan_code(subscription: ORMTenantSubscription) -> str:
    if subscription.plan:
        return subscription.plan.code
    return str(subscription.plan_id)


__all__ = [
    "to_domain_customer",
    "to_domain_feature",
    "to_domain_invoice",
    "to_domain_plan",
    "to_domain_subscription",
]
