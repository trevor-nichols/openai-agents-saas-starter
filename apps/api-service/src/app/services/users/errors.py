"""User service error hierarchy."""

from __future__ import annotations


class UserServiceError(RuntimeError):
    """Base class for user-service errors."""


class InvalidCredentialsError(UserServiceError):
    """Raised when supplied credentials fail validation."""


class UserLockedError(UserServiceError):
    """Raised when authentication is attempted against a locked user."""


class UserDisabledError(UserServiceError):
    """Raised when a disabled or pending user attempts to login."""


class TenantContextRequiredError(UserServiceError):
    """Raised when a multi-tenant user does not specify tenant context."""


class MembershipNotFoundError(UserServiceError):
    """Raised when a tenant is not associated with the user."""


class PasswordPolicyViolationError(UserServiceError):
    """Raised when a password fails the configured policy."""


class IpThrottledError(UserServiceError):
    """Raised when login attempts from an IP exceed configured limits."""


__all__ = [
    "InvalidCredentialsError",
    "IpThrottledError",
    "MembershipNotFoundError",
    "PasswordPolicyViolationError",
    "TenantContextRequiredError",
    "UserDisabledError",
    "UserLockedError",
    "UserServiceError",
]
