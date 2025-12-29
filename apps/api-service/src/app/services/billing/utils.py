"""Shared helpers for billing service workflows."""

from __future__ import annotations

from datetime import UTC, datetime


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = ["to_utc"]
