"""Common normalization helpers shared across services."""

from __future__ import annotations


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


__all__ = ["normalize_email"]
