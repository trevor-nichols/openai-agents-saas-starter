"""Identifier helpers for billing persistence."""

from __future__ import annotations

import uuid


def parse_tenant_id(value: str | None) -> uuid.UUID:
    """Validate and coerce tenant_id strings into UUIDs."""
    if not value:
        raise ValueError("Tenant identifier must be a valid UUID.")
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("Tenant identifier must be a valid UUID.") from exc


__all__ = ["parse_tenant_id"]
