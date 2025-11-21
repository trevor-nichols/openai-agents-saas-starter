from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.api.dependencies import usage as usage_dependency
from app.services.usage_policy_service import (
    UsagePolicyDecision,
    UsagePolicyResult,
    UsageViolation,
)


def test_record_guardrail_metrics_tracks_decisions(monkeypatch: pytest.MonkeyPatch) -> None:
    decisions: list[dict[str, str | None]] = []
    hits: list[dict[str, str | None]] = []

    monkeypatch.setattr(
        usage_dependency.observability_metrics,
        "record_usage_guardrail_decision",
        lambda **kwargs: decisions.append(kwargs),
    )
    monkeypatch.setattr(
        usage_dependency.observability_metrics,
        "record_usage_limit_hit",
        lambda **kwargs: hits.append(kwargs),
    )

    now = datetime(2025, 1, 1, tzinfo=UTC)
    violation = UsageViolation(
        feature_key="messages",
        limit_type="hard_limit",
        limit_value=150,
        usage=175,
        unit="messages",
        window_start=now,
        window_end=now + timedelta(days=1),
    )
    warning = UsageViolation(
        feature_key="input_tokens",
        limit_type="soft_limit",
        limit_value=100_000,
        usage=120_000,
        unit="tokens",
        window_start=now,
        window_end=now + timedelta(days=1),
    )
    result = UsagePolicyResult(
        decision=UsagePolicyDecision.HARD_LIMIT,
        window_start=now,
        window_end=now + timedelta(days=30),
        plan_code="starter",
        violations=[violation],
        warnings=[warning],
    )

    usage_dependency._record_guardrail_metrics(result)

    assert decisions == [{"decision": "hard_limit", "plan_code": "starter"}]
    assert hits == [
        {"plan_code": "starter", "limit_type": "hard_limit", "feature_key": "messages"},
        {
            "plan_code": "starter",
            "limit_type": "soft_limit",
            "feature_key": "input_tokens",
        },
    ]
