"""Prometheus metrics helpers for the auth pipeline."""

from __future__ import annotations

from typing import Final

from prometheus_client import CollectorRegistry, Counter, Histogram

REGISTRY: Final = CollectorRegistry(auto_describe=True)

_LATENCY_BUCKETS: Final = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
)


def _sanitize_token_use(value: str | None) -> str:
    if not value:
        return "unknown"
    return value.lower()


def _sanitize_account(value: str | None) -> str:
    return (value or "unknown").lower()


def _sanitize_plan_code(value: str | None) -> str:
    return (value or "unknown").lower()


def _bool_label(value: bool) -> str:
    return "true" if value else "false"


JWKS_REQUESTS_TOTAL = Counter(
    "jwks_requests_total",
    "Total number of JWKS responses served.",
    registry=REGISTRY,
)

JWKS_NOT_MODIFIED_TOTAL = Counter(
    "jwks_not_modified_total",
    "Total number of JWKS requests answered with HTTP 304.",
    registry=REGISTRY,
)

JWT_SIGNINGS_TOTAL = Counter(
    "jwt_signings_total",
    "Count of JWT signing attempts segmented by result and token_use.",
    ("result", "token_use"),
    registry=REGISTRY,
)

JWT_SIGNING_DURATION_SECONDS = Histogram(
    "jwt_signing_duration_seconds",
    "Latency histogram for JWT signing operations.",
    ("result", "token_use"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

JWT_VERIFICATIONS_TOTAL = Counter(
    "jwt_verifications_total",
    "Count of JWT verification attempts segmented by result and token_use.",
    ("result", "token_use"),
    registry=REGISTRY,
)

JWT_VERIFICATION_DURATION_SECONDS = Histogram(
    "jwt_verification_duration_seconds",
    "Latency histogram for JWT verification operations.",
    ("result", "token_use"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

SERVICE_ACCOUNT_ISSUANCE_TOTAL = Counter(
    "service_account_issuance_total",
    "Total number of service-account token issuance attempts.",
    ("account", "result", "reason", "reused"),
    registry=REGISTRY,
)

SERVICE_ACCOUNT_ISSUANCE_LATENCY_SECONDS = Histogram(
    "service_account_issuance_latency_seconds",
    "Service-account issuance latency histogram segmented by result and account.",
    ("account", "result", "reason", "reused"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

NONCE_CACHE_HITS_TOTAL = Counter(
    "nonce_cache_hits_total",
    "Number of nonce cache hits (duplicate payloads rejected).",
    registry=REGISTRY,
)

NONCE_CACHE_MISSES_TOTAL = Counter(
    "nonce_cache_misses_total",
    "Number of nonce cache misses (new payloads accepted).",
    registry=REGISTRY,
)

STRIPE_API_REQUESTS_TOTAL = Counter(
    "stripe_api_requests_total",
    "Count of Stripe API requests segmented by operation and result.",
    ("operation", "result"),
    registry=REGISTRY,
)

STRIPE_API_LATENCY_SECONDS = Histogram(
    "stripe_api_latency_seconds",
    "Latency histogram for Stripe API calls segmented by operation and result.",
    ("operation", "result"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

STRIPE_WEBHOOK_EVENTS_TOTAL = Counter(
    "stripe_webhook_events_total",
    "Count of Stripe webhook events segmented by type and result.",
    ("event_type", "result"),
    registry=REGISTRY,
)

STRIPE_GATEWAY_OPERATIONS_TOTAL = Counter(
    "stripe_gateway_operations_total",
    "Count of Stripe gateway operations segmented by operation, plan_code, and result.",
    ("operation", "plan_code", "result"),
    registry=REGISTRY,
)

STRIPE_GATEWAY_OPERATION_DURATION_SECONDS = Histogram(
    "stripe_gateway_operation_duration_seconds",
    "Latency histogram for Stripe gateway operations segmented by operation, plan_code, and result.",
    ("operation", "plan_code", "result"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)


def observe_jwt_signing(*, result: str, token_use: str | None, duration_seconds: float) -> None:
    label = _sanitize_token_use(token_use)
    JWT_SIGNINGS_TOTAL.labels(result=result, token_use=label).inc()
    JWT_SIGNING_DURATION_SECONDS.labels(result=result, token_use=label).observe(max(duration_seconds, 0.0))


def observe_jwt_verification(
    *,
    result: str,
    token_use: str | None,
    duration_seconds: float,
) -> None:
    label = _sanitize_token_use(token_use)
    JWT_VERIFICATIONS_TOTAL.labels(result=result, token_use=label).inc()
    JWT_VERIFICATION_DURATION_SECONDS.labels(result=result, token_use=label).observe(
        max(duration_seconds, 0.0)
    )


def observe_service_account_issuance(
    *,
    account: str | None,
    result: str,
    reason: str,
    reused: bool,
    duration_seconds: float,
) -> None:
    account_label = _sanitize_account(account)
    reused_label = _bool_label(reused)
    SERVICE_ACCOUNT_ISSUANCE_TOTAL.labels(
        account=account_label,
        result=result,
        reason=reason,
        reused=reused_label,
    ).inc()
    SERVICE_ACCOUNT_ISSUANCE_LATENCY_SECONDS.labels(
        account=account_label,
        result=result,
        reason=reason,
        reused=reused_label,
    ).observe(max(duration_seconds, 0.0))


def record_nonce_cache_result(*, hit: bool) -> None:
    if hit:
        NONCE_CACHE_HITS_TOTAL.inc()
    else:
        NONCE_CACHE_MISSES_TOTAL.inc()


def observe_stripe_api_call(*, operation: str, result: str, duration_seconds: float) -> None:
    STRIPE_API_REQUESTS_TOTAL.labels(operation=operation, result=result).inc()
    STRIPE_API_LATENCY_SECONDS.labels(operation=operation, result=result).observe(max(duration_seconds, 0.0))


def observe_stripe_webhook_event(*, event_type: str, result: str) -> None:
    STRIPE_WEBHOOK_EVENTS_TOTAL.labels(event_type=event_type or "unknown", result=result).inc()


def observe_stripe_gateway_operation(
    *,
    operation: str,
    plan_code: str | None,
    result: str,
    duration_seconds: float,
) -> None:
    plan_label = _sanitize_plan_code(plan_code)
    STRIPE_GATEWAY_OPERATIONS_TOTAL.labels(operation=operation, plan_code=plan_label, result=result).inc()
    STRIPE_GATEWAY_OPERATION_DURATION_SECONDS.labels(
        operation=operation,
        plan_code=plan_label,
        result=result,
    ).observe(max(duration_seconds, 0.0))
