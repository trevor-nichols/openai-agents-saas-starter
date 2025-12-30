"""Payment gateway contracts and DTOs."""

from __future__ import annotations

from .factory import get_payment_gateway
from .fixture_gateway import FixtureGateway, get_fixture_gateway
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
from .protocol import PaymentGateway, PaymentGatewayError

__all__ = [
    "CustomerProvisionResult",
    "FixtureGateway",
    "PaymentGateway",
    "PaymentGatewayError",
    "PaymentMethodSummary",
    "PortalSessionResult",
    "SetupIntentResult",
    "SubscriptionPlanScheduleResult",
    "SubscriptionPlanSwapResult",
    "SubscriptionProvisionResult",
    "UpcomingInvoiceLine",
    "UpcomingInvoicePreviewResult",
    "get_fixture_gateway",
    "get_payment_gateway",
]
