"""Utility helpers for vector store services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


def coerce_uuid(value: uuid.UUID | str | None) -> uuid.UUID:
    if value is None:
        raise ValueError("UUID value is required")
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # pragma: no cover - validation
        raise ValueError(f"Invalid UUID value: {value}") from exc


def coerce_uuid_optional(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None:
        return None
    return coerce_uuid(value)

def coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except Exception:
            return None
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except Exception:
        return None


__all__ = ["coerce_uuid", "coerce_uuid_optional", "coerce_datetime"]
