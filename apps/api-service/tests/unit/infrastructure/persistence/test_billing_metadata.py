from __future__ import annotations

from datetime import UTC, datetime

from typing import cast

from app.domain.billing import TenantSubscription
from app.infrastructure.persistence.billing.metadata import (
    coerce_int,
    parse_metadata_datetime,
    serialize_subscription_metadata,
)


def _subscription(**overrides: object) -> TenantSubscription:
    payload: dict[str, object] = {
        "tenant_id": "3c9e9a10-89c1-4f0e-8cd1-6230b5b6cc6a",
        "plan_code": "starter",
        "status": "active",
        "auto_renew": True,
        "billing_email": "billing@example.com",
        "starts_at": datetime(2025, 1, 1, tzinfo=UTC),
        "current_period_start": None,
        "current_period_end": None,
        "trial_ends_at": None,
        "cancel_at": None,
        "seat_count": None,
        "pending_plan_code": None,
        "pending_plan_effective_at": None,
        "pending_seat_count": None,
        "metadata": {"keep": "value"},
        "processor": None,
        "processor_customer_id": None,
        "processor_subscription_id": None,
        "processor_schedule_id": None,
    }
    payload.update(overrides)
    return TenantSubscription(
        tenant_id=cast(str, payload["tenant_id"]),
        plan_code=cast(str, payload["plan_code"]),
        status=cast(str, payload["status"]),
        auto_renew=cast(bool, payload["auto_renew"]),
        billing_email=cast(str | None, payload["billing_email"]),
        starts_at=cast(datetime, payload["starts_at"]),
        current_period_start=cast(datetime | None, payload["current_period_start"]),
        current_period_end=cast(datetime | None, payload["current_period_end"]),
        trial_ends_at=cast(datetime | None, payload["trial_ends_at"]),
        cancel_at=cast(datetime | None, payload["cancel_at"]),
        seat_count=cast(int | None, payload["seat_count"]),
        pending_plan_code=cast(str | None, payload["pending_plan_code"]),
        pending_plan_effective_at=cast(datetime | None, payload["pending_plan_effective_at"]),
        pending_seat_count=cast(int | None, payload["pending_seat_count"]),
        metadata=cast(dict[str, str], payload["metadata"]),
        processor=cast(str | None, payload["processor"]),
        processor_customer_id=cast(str | None, payload["processor_customer_id"]),
        processor_subscription_id=cast(str | None, payload["processor_subscription_id"]),
        processor_schedule_id=cast(str | None, payload["processor_schedule_id"]),
    )


def test_serialize_subscription_metadata_removes_empty_fields() -> None:
    subscription = _subscription(
        pending_plan_code="",
        processor_schedule_id="",
        pending_plan_effective_at=None,
        pending_seat_count=None,
    )

    metadata = serialize_subscription_metadata(subscription)

    assert metadata == {"keep": "value"}


def test_serialize_subscription_metadata_formats_datetimes() -> None:
    naive_effective_at = datetime(2025, 2, 3, 4, 5, 6)
    subscription = _subscription(
        pending_plan_code="pro",
        pending_plan_effective_at=naive_effective_at,
    )

    metadata = serialize_subscription_metadata(subscription)

    assert metadata["pending_plan_code"] == "pro"
    effective_at = metadata["pending_plan_effective_at"]
    assert isinstance(effective_at, str)
    assert effective_at.endswith("+00:00")


def test_parse_metadata_datetime_handles_strings_and_naive() -> None:
    parsed = parse_metadata_datetime("2025-01-02T03:04:05")

    assert parsed is not None
    assert parsed.tzinfo is UTC


def test_coerce_int_handles_multiple_types() -> None:
    assert coerce_int("12") == 12
    assert coerce_int(12.7) == 12
    assert coerce_int(None) is None
