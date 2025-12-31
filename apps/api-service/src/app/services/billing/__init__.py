"""Billing service barrel exports (subscriptions, invoices, payments)."""

from __future__ import annotations

from .billing_events import (
    BillingEventBackend,
    BillingEventHistoryPage,
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventsService,
    BillingEventStream,
    BillingEventSubscription,
    BillingEventUsage,
    billing_events_service,
    get_billing_events_service,
)
from .billing_service import BillingService
from .errors import (
    BillingError,
    InvalidTenantIdentifierError,
    PaymentProviderError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
)
from .models import (
    PlanChangeResult,
    PlanChangeTiming,
    ProcessorInvoiceLineSnapshot,
    ProcessorInvoiceSnapshot,
    ProcessorSubscriptionSnapshot,
    UpcomingInvoiceLineSnapshot,
    UpcomingInvoicePreview,
)
from .payment_gateway import (
    FixtureGateway,
    PaymentGateway,
    PaymentGatewayError,
    SubscriptionProvisionResult,
    get_fixture_gateway,
    get_payment_gateway,
)
from .stripe.gateway import StripeGateway, get_stripe_gateway

__all__ = [
    "BillingEventBackend",
    "BillingEventHistoryPage",
    "BillingEventInvoice",
    "BillingEventPayload",
    "BillingEventStream",
    "BillingEventSubscription",
    "BillingEventUsage",
    "BillingEventsService",
    "BillingError",
    "BillingService",
    "FixtureGateway",
    "InvalidTenantIdentifierError",
    "PaymentGateway",
    "PaymentGatewayError",
    "PaymentProviderError",
    "PlanNotFoundError",
    "PlanChangeResult",
    "PlanChangeTiming",
    "ProcessorInvoiceLineSnapshot",
    "ProcessorInvoiceSnapshot",
    "ProcessorSubscriptionSnapshot",
    "StripeGateway",
    "SubscriptionNotFoundError",
    "SubscriptionProvisionResult",
    "SubscriptionStateError",
    "UpcomingInvoiceLineSnapshot",
    "UpcomingInvoicePreview",
    "billing_events_service",
    "get_fixture_gateway",
    "get_payment_gateway",
    "get_billing_events_service",
    "get_stripe_gateway",
]
