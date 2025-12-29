"""Billing service errors and mapping helpers."""

from __future__ import annotations

from typing import NoReturn

from app.services.billing.payment_gateway import PaymentGatewayError


class BillingError(Exception):
    """Base class for billing-related failures."""


class PlanNotFoundError(BillingError):
    """Raised when the requested plan does not exist."""


class SubscriptionNotFoundError(BillingError):
    """Raised when no subscription exists for the tenant."""


class SubscriptionStateError(BillingError):
    """Raised when subscription state prevents the requested operation."""


class BillingCustomerNotFoundError(BillingError):
    """Raised when no billing customer exists for the tenant."""


class InvalidTenantIdentifierError(BillingError):
    """Raised when the provided tenant identifier is not valid for persistence."""


class PaymentProviderError(BillingError):
    """Raised when the payment gateway rejects a request."""


def raise_invalid_tenant(exc: ValueError) -> NoReturn:
    """Promote repository ValueErrors into domain-specific billing errors."""

    raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc


def raise_payment_provider(exc: PaymentGatewayError) -> NoReturn:
    """Promote gateway failures into domain-specific billing errors."""

    raise PaymentProviderError(str(exc)) from exc


__all__ = [
    "BillingCustomerNotFoundError",
    "BillingError",
    "InvalidTenantIdentifierError",
    "PaymentProviderError",
    "PlanNotFoundError",
    "SubscriptionNotFoundError",
    "SubscriptionStateError",
    "raise_invalid_tenant",
    "raise_payment_provider",
]
