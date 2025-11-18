"""Unit tests for observability metric helpers."""

from __future__ import annotations

from typing import Any, cast

import pytest

from app.observability import metrics


def _reset_metric(metric: Any) -> None:
    metrics = getattr(metric, "_metrics", None)
    if metrics is not None:
        metrics.clear()
    value = getattr(metric, "_value", None)
    if value is not None:
        value.set(0)


def test_observe_jwt_verification_records_labels() -> None:
    _reset_metric(metrics.JWT_VERIFICATIONS_TOTAL)
    _reset_metric(metrics.JWT_VERIFICATION_DURATION_SECONDS)

    metrics.observe_jwt_verification(result="success", token_use="refresh", duration_seconds=0.05)

    counter_child = metrics.JWT_VERIFICATIONS_TOTAL.labels(result="success", token_use="refresh")
    histogram_child = metrics.JWT_VERIFICATION_DURATION_SECONDS.labels(
        result="success", token_use="refresh"
    )

    counter_internal = cast(Any, counter_child)
    histogram_internal = cast(Any, histogram_child)
    assert counter_internal._value.get() == 1
    assert histogram_internal._sum.get() == pytest.approx(0.05, rel=1e-3)


def test_observe_service_account_issuance_tracks_reason() -> None:
    _reset_metric(metrics.SERVICE_ACCOUNT_ISSUANCE_TOTAL)
    _reset_metric(metrics.SERVICE_ACCOUNT_ISSUANCE_LATENCY_SECONDS)

    metrics.observe_service_account_issuance(
        account="billing-worker",
        result="failure",
        reason="rate_limited",
        reused=False,
        duration_seconds=0.2,
    )

    counter_child = metrics.SERVICE_ACCOUNT_ISSUANCE_TOTAL.labels(
        account="billing-worker",
        result="failure",
        reason="rate_limited",
        reused="false",
    )
    counter_internal = cast(Any, counter_child)
    assert counter_internal._value.get() == 1


def test_record_nonce_cache_result_increments_counters() -> None:
    _reset_metric(metrics.NONCE_CACHE_HITS_TOTAL)
    _reset_metric(metrics.NONCE_CACHE_MISSES_TOTAL)

    metrics.record_nonce_cache_result(hit=False)
    metrics.record_nonce_cache_result(hit=True)

    misses = cast(Any, metrics.NONCE_CACHE_MISSES_TOTAL)
    hits = cast(Any, metrics.NONCE_CACHE_HITS_TOTAL)
    assert misses._value.get() == 1
    assert hits._value.get() == 1


def test_observe_stripe_gateway_operation_records_labels() -> None:
    _reset_metric(metrics.STRIPE_GATEWAY_OPERATIONS_TOTAL)
    _reset_metric(metrics.STRIPE_GATEWAY_OPERATION_DURATION_SECONDS)

    metrics.observe_stripe_gateway_operation(
        operation="start_subscription",
        plan_code="Starter",
        result="success",
        duration_seconds=0.1,
    )

    counter_child = metrics.STRIPE_GATEWAY_OPERATIONS_TOTAL.labels(
        operation="start_subscription",
        plan_code="starter",
        result="success",
    )
    counter_internal = cast(Any, counter_child)
    assert counter_internal._value.get() == 1


def test_record_usage_guardrail_decision_normalizes_plan_code() -> None:
    _reset_metric(metrics.USAGE_GUARDRAIL_DECISIONS_TOTAL)

    metrics.record_usage_guardrail_decision(decision="allow", plan_code="Starter")

    counter_child = metrics.USAGE_GUARDRAIL_DECISIONS_TOTAL.labels(
        decision="allow",
        plan_code="starter",
    )
    counter_internal = cast(Any, counter_child)
    assert counter_internal._value.get() == 1


def test_record_usage_limit_hit_tracks_feature_and_limit() -> None:
    _reset_metric(metrics.USAGE_LIMIT_HITS_TOTAL)

    metrics.record_usage_limit_hit(
        plan_code="pro",
        limit_type="hard_limit",
        feature_key="messages",
    )

    counter_child = metrics.USAGE_LIMIT_HITS_TOTAL.labels(
        plan_code="pro",
        limit_type="hard_limit",
        feature_key="messages",
    )
    counter_internal = cast(Any, counter_child)
    assert counter_internal._value.get() == 1
