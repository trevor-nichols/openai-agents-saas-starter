"""Signup service error types."""

from __future__ import annotations


class SignupServiceError(RuntimeError):
    """Base error for signup orchestration."""


class PublicSignupDisabledError(SignupServiceError):
    """Raised when public signup is disabled via configuration."""


class TenantSlugCollisionError(SignupServiceError):
    """Raised when a tenant slug cannot be provisioned."""


class EmailAlreadyRegisteredError(SignupServiceError):
    """Raised when the supplied email already exists."""


class BillingProvisioningError(SignupServiceError):
    """Raised when billing fails during signup."""


__all__ = [
    "BillingProvisioningError",
    "EmailAlreadyRegisteredError",
    "PublicSignupDisabledError",
    "SignupServiceError",
    "TenantSlugCollisionError",
]
