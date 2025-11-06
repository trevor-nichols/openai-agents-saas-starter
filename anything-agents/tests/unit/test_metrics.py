"""Unit tests for observability metric helpers."""

from __future__ import annotations

import pytest

from app.observability import metrics


def _reset_metric(metric) -> None:  # type: ignore[no-untyped-def]
    if hasattr(metric, "_metrics"):
        metric._metrics.clear()
    if hasattr(metric, "_value"):
        metric._value.set(0)  # type: ignore[attr-defined]


def test_observe_jwt_verification_records_labels() -> None:
    _reset_metric(metrics.JWT_VERIFICATIONS_TOTAL)
    _reset_metric(metrics.JWT_VERIFICATION_DURATION_SECONDS)

    metrics.observe_jwt_verification(result="success", token_use="refresh", duration_seconds=0.05)

    counter_child = metrics.JWT_VERIFICATIONS_TOTAL.labels(result="success", token_use="refresh")
    histogram_child = metrics.JWT_VERIFICATION_DURATION_SECONDS.labels(
        result="success", token_use="refresh"
    )

    assert counter_child._value.get() == 1  # type: ignore[attr-defined]
    assert histogram_child._sum.get() == pytest.approx(0.05, rel=1e-3)  # type: ignore[attr-defined]


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
    assert counter_child._value.get() == 1  # type: ignore[attr-defined]


def test_record_nonce_cache_result_increments_counters() -> None:
    _reset_metric(metrics.NONCE_CACHE_HITS_TOTAL)
    _reset_metric(metrics.NONCE_CACHE_MISSES_TOTAL)

    metrics.record_nonce_cache_result(hit=False)
    metrics.record_nonce_cache_result(hit=True)

    assert metrics.NONCE_CACHE_MISSES_TOTAL._value.get() == 1  # type: ignore[attr-defined]
    assert metrics.NONCE_CACHE_HITS_TOTAL._value.get() == 1  # type: ignore[attr-defined]
