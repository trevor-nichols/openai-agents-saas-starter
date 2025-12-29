"""Shared telemetry wrapper for Stripe gateway operations."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

from app.infrastructure.stripe import StripeClientError
from app.observability.metrics import observe_stripe_gateway_operation
from app.services.billing.payment_gateway import PaymentGatewayError

logger = logging.getLogger("api-service.services.payment_gateway")

T = TypeVar("T")


def _base_context(
    *,
    operation: str,
    plan_code: str | None,
    tenant_id: str | None,
    subscription_id: str | None,
    context: dict[str, object] | None,
) -> dict[str, object]:
    base: dict[str, object] = {
        "stripe_gateway_operation": operation,
    }
    if plan_code:
        base["plan_code"] = plan_code
    if tenant_id:
        base["tenant_id"] = tenant_id
    if subscription_id:
        base["subscription_id"] = subscription_id
    if context:
        for key, value in context.items():
            if value is not None:
                base[key] = value
    return base


async def execute_gateway_operation(
    *,
    operation: str,
    plan_code: str | None,
    tenant_id: str | None,
    subscription_id: str | None,
    context: dict[str, object] | None,
    action: Callable[[], Awaitable[T]],
) -> T:
    base_context = _base_context(
        operation=operation,
        plan_code=plan_code,
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        context=context,
    )

    logger.info("Stripe gateway operation started", extra=base_context)
    start = perf_counter()

    try:
        result = await action()
    except PaymentGatewayError as exc:
        duration = perf_counter() - start
        observe_stripe_gateway_operation(
            operation=operation,
            plan_code=plan_code,
            result=exc.code or "error",
            duration_seconds=duration,
        )
        failure_context = {
            **base_context,
            "duration_ms": int(duration * 1000),
            "error": str(exc),
            "error_code": exc.code or "error",
        }
        logger.warning("Stripe gateway operation failed", extra=failure_context)
        raise
    except StripeClientError as exc:
        duration = perf_counter() - start
        error_code = exc.code or "stripe_error"
        observe_stripe_gateway_operation(
            operation=operation,
            plan_code=plan_code,
            result=error_code,
            duration_seconds=duration,
        )
        failure_context = {
            **base_context,
            "duration_ms": int(duration * 1000),
            "error": str(exc),
            "error_code": error_code,
        }
        logger.error("Stripe API error during gateway operation", extra=failure_context)
        raise PaymentGatewayError(
            f"Stripe error during {operation}: {exc}", code=error_code
        ) from exc
    except Exception:
        duration = perf_counter() - start
        observe_stripe_gateway_operation(
            operation=operation,
            plan_code=plan_code,
            result="exception",
            duration_seconds=duration,
        )
        logger.exception(
            "Unexpected Stripe gateway failure",
            extra={**base_context, "duration_ms": int(duration * 1000)},
        )
        raise
    else:
        duration = perf_counter() - start
        observe_stripe_gateway_operation(
            operation=operation,
            plan_code=plan_code,
            result="success",
            duration_seconds=duration,
        )
        logger.info(
            "Stripe gateway operation completed",
            extra={**base_context, "duration_ms": int(duration * 1000)},
        )
        return result


__all__ = ["execute_gateway_operation"]
