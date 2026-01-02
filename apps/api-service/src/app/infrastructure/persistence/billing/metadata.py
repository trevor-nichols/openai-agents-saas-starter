"""Serialization helpers for billing subscription metadata."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.billing import TenantSubscription


def serialize_subscription_metadata(subscription: TenantSubscription) -> dict[str, object]:
    metadata: dict[str, object] = dict(subscription.metadata or {})
    _set_metadata_value(metadata, "processor_schedule_id", subscription.processor_schedule_id)
    _set_metadata_value(metadata, "pending_plan_code", subscription.pending_plan_code)
    _set_metadata_value(
        metadata,
        "pending_plan_effective_at",
        _format_metadata_datetime(subscription.pending_plan_effective_at),
    )
    _set_metadata_value(metadata, "pending_seat_count", subscription.pending_seat_count)
    return metadata


def parse_metadata_datetime(value: object | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def coerce_int(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int | float | str):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def _set_metadata_value(metadata: dict[str, object], key: str, value: object | None) -> None:
    if value is None or value == "":
        metadata.pop(key, None)
        return
    metadata[key] = value


def _format_metadata_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


__all__ = ["coerce_int", "parse_metadata_datetime", "serialize_subscription_metadata"]
