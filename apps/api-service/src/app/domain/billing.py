"""Domain entities and repository contracts for billing/subscription data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class PlanFeature:
    key: str
    display_name: str
    description: str | None = None
    hard_limit: int | None = None
    soft_limit: int | None = None
    is_metered: bool = False


@dataclass(slots=True)
class BillingPlan:
    code: str
    name: str
    interval: str
    interval_count: int
    price_cents: int
    currency: str
    trial_days: int | None = None
    seat_included: int | None = None
    feature_toggles: dict[str, bool] = field(default_factory=dict)
    features: list[PlanFeature] = field(default_factory=list)
    is_active: bool = True


@dataclass(slots=True)
class TenantSubscription:
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
    metadata: dict[str, str] = field(default_factory=dict)
    processor: str | None = None
    processor_customer_id: str | None = None
    processor_subscription_id: str | None = None


@dataclass(slots=True)
class BillingCustomerRecord:
    tenant_id: str
    processor: str
    processor_customer_id: str
    billing_email: str | None = None


@dataclass(slots=True)
class SubscriptionInvoiceRecord:
    tenant_id: str
    period_start: datetime
    period_end: datetime
    amount_cents: int
    currency: str
    status: str
    processor_invoice_id: str | None = None
    hosted_invoice_url: str | None = None


class BillingRepository(Protocol):
    """Persistence contract for billing plan and subscription data."""

    async def list_plans(self) -> list[BillingPlan]: ...

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None: ...

    async def upsert_subscription(self, subscription: TenantSubscription) -> None: ...

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription: ...

    async def get_customer(
        self, tenant_id: str, *, processor: str
    ) -> BillingCustomerRecord | None: ...

    async def upsert_customer(
        self, customer: BillingCustomerRecord
    ) -> BillingCustomerRecord: ...

    async def record_usage(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None: ...

    async def record_usage_from_processor(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None: ...

    async def upsert_invoice(self, invoice: SubscriptionInvoiceRecord) -> None: ...

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: Sequence[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]: ...


@dataclass(slots=True)
class UsageTotal:
    feature_key: str
    unit: str
    quantity: int
    window_start: datetime
    window_end: datetime
