"""Retrying request executor for Stripe API calls."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Callable
from typing import Any

from app.infrastructure.stripe.errors import (
    RETRYABLE_ERRORS,
    StripeClientError,
    StripeLibraryError,
    stripe_error_code,
    stripe_user_message,
)
from app.observability.metrics import observe_stripe_api_call

logger = logging.getLogger("api-service.infrastructure.stripe")


class StripeRequestExecutor:
    """Runs Stripe SDK calls with retries, metrics, and error translation."""

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        initial_backoff_seconds: float = 0.5,
        retryable_errors: tuple[type[Exception], ...] = RETRYABLE_ERRORS,
    ) -> None:
        self._max_attempts = max(1, max_attempts)
        self._initial_backoff = max(0.1, initial_backoff_seconds)
        self._retryable_errors = retryable_errors

    async def request(self, operation: str, func: Callable[[], Any]) -> Any:
        attempt = 0
        last_error: Exception | None = None
        while attempt < self._max_attempts:
            attempt += 1
            start = time.perf_counter()
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, func)
                observe_stripe_api_call(
                    operation=operation,
                    result="success",
                    duration_seconds=time.perf_counter() - start,
                )
                return result
            except StripeLibraryError as exc:
                observe_stripe_api_call(
                    operation=operation,
                    result=stripe_error_code(exc),
                    duration_seconds=time.perf_counter() - start,
                )
                logger.warning(
                    "Stripe API error on %s (attempt %s/%s): %s",
                    operation,
                    attempt,
                    self._max_attempts,
                    stripe_user_message(exc),
                )
                if attempt >= self._max_attempts or not self._should_retry(exc):
                    raise StripeClientError(
                        operation, stripe_user_message(exc), code=stripe_error_code(exc)
                    ) from exc
                await asyncio.sleep(self._backoff(attempt))
                last_error = exc
            except Exception as exc:  # pragma: no cover - unexpected runtime failure
                observe_stripe_api_call(
                    operation=operation,
                    result="exception",
                    duration_seconds=time.perf_counter() - start,
                )
                logger.exception("Unexpected error during Stripe operation %s", operation)
                raise StripeClientError(operation, str(exc)) from exc
        raise StripeClientError(operation, str(last_error or "Unknown Stripe error"))

    def _backoff(self, attempt: int) -> float:
        jitter = random.uniform(0, self._initial_backoff)
        return self._initial_backoff * (2 ** (attempt - 1)) + jitter

    def _should_retry(self, exc: Exception) -> bool:
        return isinstance(exc, self._retryable_errors)


__all__ = ["StripeRequestExecutor"]
