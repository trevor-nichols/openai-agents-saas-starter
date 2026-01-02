"""Errors raised during SSO orchestration."""

from __future__ import annotations


class SsoServiceError(RuntimeError):
    """Base class for SSO service errors."""

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class SsoConfigurationError(SsoServiceError):
    """Raised when SSO is not configured or disabled for a tenant."""


class SsoStateError(SsoServiceError):
    """Raised when SSO state or nonce validation fails."""


class SsoTokenError(SsoServiceError):
    """Raised when token exchange or verification fails."""


class SsoIdentityError(SsoServiceError):
    """Raised when identity linkage fails or conflicts."""


class SsoProvisioningError(SsoServiceError):
    """Raised when auto-provisioning rules block the login."""


__all__ = [
    "SsoConfigurationError",
    "SsoIdentityError",
    "SsoProvisioningError",
    "SsoServiceError",
    "SsoStateError",
    "SsoTokenError",
]
