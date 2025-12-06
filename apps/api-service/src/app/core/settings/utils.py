"""Utility helpers shared across settings mixins."""
from __future__ import annotations


def normalize_url(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None
