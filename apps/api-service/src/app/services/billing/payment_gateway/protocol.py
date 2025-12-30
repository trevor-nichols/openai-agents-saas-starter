"""Gateway protocol and shared gateway errors."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .models import (
    CustomerProvisionResult,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
    SubscriptionPlanScheduleResult,
    SubscriptionPlanSwapResult,
    SubscriptionProvisionResult,
    UpcomingInvoicePreviewResult,
)


class PaymentGateway(Protocol):
    """Interface for subscription lifecycle interactions with a payment provider."""

    processor_name: str

    async def create_customer(
        self,
        *,
        tenant_id: str,
        billing_email: str | None,
    ) -> CustomerProvisionResult: ...

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
    ) -> SubscriptionProvisionResult: ...

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None: ...

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None: ...

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None: ...

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSessionResult: ...

    async def list_payment_methods(
        self, *, customer_id: str
    ) -> list[PaymentMethodSummary]: ...

    async def create_setup_intent(
        self, *, customer_id: str
    ) -> SetupIntentResult: ...

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None: ...

    async def detach_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None: ...

    async def preview_upcoming_invoice(
        self,
        *,
        subscription_id: str,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> UpcomingInvoicePreviewResult: ...

    async def swap_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
        schedule_id: str | None = None,
        proration_behavior: str | None = None,
    ) -> SubscriptionPlanSwapResult: ...

    async def schedule_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
    ) -> SubscriptionPlanScheduleResult: ...


class PaymentGatewayError(RuntimeError):
    """Raised when the payment provider returns a fatal error."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


__all__ = ["PaymentGateway", "PaymentGatewayError"]
