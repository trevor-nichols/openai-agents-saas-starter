"""Shared error types for authentication services."""

from __future__ import annotations


class ServiceAccountError(RuntimeError):
    """Base class for service-account issuance errors."""


class ServiceAccountValidationError(ServiceAccountError):
    """Raised when the request fails validation checks."""


class ServiceAccountRateLimitError(ServiceAccountError):
    """Raised when issuance requests exceed configured limits."""


class ServiceAccountCatalogUnavailable(ServiceAccountError):
    """Raised when the service-account catalog cannot be loaded."""


class UserAuthenticationError(RuntimeError):
    """Base class for human authentication failures."""


class UserRefreshError(UserAuthenticationError):
    """Raised when refresh tokens fail validation."""


class UserLogoutError(UserAuthenticationError):
    """Raised when logout operations fail."""


class MfaRequiredError(UserAuthenticationError):
    """Raised when login requires an MFA challenge before issuing tokens."""

    def __init__(self, challenge_token: str, methods: list[dict[str, object]]) -> None:
        super().__init__("Multi-factor authentication required.")
        self.challenge_token = challenge_token
        self.methods = methods
