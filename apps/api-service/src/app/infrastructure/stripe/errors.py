"""Stripe error helpers and retryable error configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import stripe

StripeLibraryError = cast(
    type[Exception], getattr(getattr(stripe, "error", None), "StripeError", Exception)
)


class StripeClientError(RuntimeError):
    """Wrapper for unrecoverable Stripe API failures."""

    def __init__(self, operation: str, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.operation = operation
        self.code = code


if TYPE_CHECKING:

    class StripeAPIConnectionError(Exception):
        ...

    class StripeAPIError(Exception):
        ...

    class StripeRateLimitError(Exception):
        ...

    class StripeIdempotencyError(Exception):
        ...

else:
    _stripe_error_ns = getattr(stripe, "error", None)

    def _resolve_error(name: str) -> type[Exception]:
        candidate = getattr(_stripe_error_ns, name, None) if _stripe_error_ns else None
        if isinstance(candidate, type):
            return cast(type[Exception], candidate)
        return Exception

    StripeAPIConnectionError = _resolve_error("APIConnectionError")
    StripeAPIError = _resolve_error("APIError")
    StripeRateLimitError = _resolve_error("RateLimitError")
    StripeIdempotencyError = _resolve_error("IdempotencyError")


RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    StripeAPIConnectionError,
    StripeAPIError,
    StripeRateLimitError,
    StripeIdempotencyError,
)


def stripe_error_code(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code:
        return str(code)
    error_obj = getattr(exc, "error", None)
    if error_obj is not None:
        error_type = getattr(error_obj, "type", None)
        if error_type:
            return str(error_type)
    return exc.__class__.__name__


def stripe_user_message(exc: Exception) -> str:
    message = getattr(exc, "user_message", None)
    if message:
        return str(message)
    return str(exc)


__all__ = [
    "RETRYABLE_ERRORS",
    "StripeClientError",
    "StripeLibraryError",
    "stripe_error_code",
    "stripe_user_message",
]
