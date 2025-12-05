"""Utility helpers for vector store services."""

from __future__ import annotations

import uuid


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


__all__ = ["coerce_uuid", "coerce_uuid_optional"]
