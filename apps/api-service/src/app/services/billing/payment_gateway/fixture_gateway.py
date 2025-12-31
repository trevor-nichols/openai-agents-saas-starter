"""Fixture-backed payment gateway for deterministic test environments."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .models import (
    CustomerProvisionResult,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
    SubscriptionPlanScheduleResult,
    SubscriptionPlanSwapResult,
    SubscriptionProvisionResult,
    UpcomingInvoiceLine,
    UpcomingInvoicePreviewResult,
)
from .protocol import PaymentGateway


class FixtureGateway(PaymentGateway):
    """No-op gateway that returns deterministic fixture payloads."""

    processor_name = "fixture"

    def __init__(self, *, now_factory: Callable[[], datetime] | None = None) -> None:
        self._now_factory = now_factory or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        return self._now_factory()

    def _period_end(self, start: datetime | None = None) -> datetime:
        base = start or self._now()
        return base + timedelta(days=30)

    async def create_customer(
        self,
        *,
        tenant_id: str,
        billing_email: str | None,
    ) -> CustomerProvisionResult:
        customer_id = f"fixture-{tenant_id}"
        return CustomerProvisionResult(
            processor=self.processor_name,
            customer_id=customer_id,
            billing_email=billing_email,
        )

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
        customer_id: str | None = None,
    ) -> SubscriptionProvisionResult:
        now = self._now()
        trial_ends = now + timedelta(days=trial_days) if trial_days and trial_days > 0 else None
        return SubscriptionProvisionResult(
            processor=self.processor_name,
            customer_id=customer_id or f"fixture-{tenant_id}",
            subscription_id=f"fixture-sub-{tenant_id}",
            starts_at=now,
            current_period_start=now,
            current_period_end=self._period_end(now),
            trial_ends_at=trial_ends,
            metadata={"fixture": "true", "plan_code": plan_code},
        )

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None:
        return None

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        return None

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        return None

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSessionResult:
        return PortalSessionResult(url=return_url)

    async def list_payment_methods(
        self, *, customer_id: str
    ) -> list[PaymentMethodSummary]:
        return []

    async def create_setup_intent(
        self, *, customer_id: str
    ) -> SetupIntentResult:
        return SetupIntentResult(
            id=f"fixture-setup-{uuid4()}",
            client_secret=f"fixture-secret-{uuid4()}",
        )

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        return None

    async def detach_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        return None

    async def preview_upcoming_invoice(
        self,
        *,
        subscription_id: str,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> UpcomingInvoicePreviewResult:
        now = self._now()
        quantity = seat_count or 1
        line = UpcomingInvoiceLine(
            description="Fixture invoice preview",
            amount_cents=0,
            currency="usd",
            quantity=quantity,
            unit_amount_cents=0,
            price_id=f"fixture-price-{subscription_id}",
        )
        return UpcomingInvoicePreviewResult(
            invoice_id=f"fixture-invoice-{subscription_id}",
            amount_due_cents=0,
            currency="usd",
            period_start=now,
            period_end=self._period_end(now),
            lines=[line],
        )

    async def swap_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
        schedule_id: str | None = None,
        proration_behavior: str | None = None,
    ) -> SubscriptionPlanSwapResult:
        now = self._now()
        return SubscriptionPlanSwapResult(
            price_id=f"fixture-price-{plan_code}",
            subscription_item_id=f"fixture-item-{subscription_id}",
            current_period_start=now,
            current_period_end=self._period_end(now),
            quantity=seat_count,
            metadata={"fixture": "true", "plan_code": plan_code},
        )

    async def schedule_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
    ) -> SubscriptionPlanScheduleResult:
        now = self._now()
        return SubscriptionPlanScheduleResult(
            schedule_id=f"fixture-schedule-{subscription_id}",
            price_id=f"fixture-price-{plan_code}",
            current_period_start=now,
            current_period_end=self._period_end(now),
            quantity=seat_count,
            metadata={"fixture": "true", "plan_code": plan_code},
        )


_fixture_gateway: FixtureGateway | None = None


def get_fixture_gateway() -> FixtureGateway:
    """Return a shared fixture gateway instance."""

    global _fixture_gateway
    if _fixture_gateway is None:
        _fixture_gateway = FixtureGateway()
    return _fixture_gateway


__all__ = ["FixtureGateway", "get_fixture_gateway"]
