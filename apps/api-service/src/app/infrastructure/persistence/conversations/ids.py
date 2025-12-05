"""Helpers for normalizing conversation and tenant identifiers."""

from __future__ import annotations

import uuid

_CONVERSATION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "api-service:conversation")


def coerce_conversation_uuid(conversation_id: str) -> uuid.UUID:
    """Normalize external conversation id into a UUID.

    - Accepts canonical UUIDs.
    - Accepts arbitrary strings via namespace UUID for deterministic mapping.
    - Falls back to a random UUID when empty.
    """
    if not conversation_id:
        return uuid.uuid4()
    try:
        return uuid.UUID(conversation_id)
    except (TypeError, ValueError):
        return uuid.uuid5(_CONVERSATION_NAMESPACE, conversation_id)


def derive_conversation_key(conversation_id: str) -> str:
    """Return a stable key suitable for uniqueness constraint (<=255 chars)."""
    if not conversation_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(conversation_id))
    except (TypeError, ValueError):
        if len(conversation_id) > 255:
            raise ValueError("Conversation identifier must be 255 characters or fewer.") from None
        return conversation_id


def parse_tenant_id(value: str | None) -> uuid.UUID:
    """Validate and coerce tenant_id strings into UUIDs."""
    if not value:
        raise ValueError("tenant_id is required")
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - invalid user input
        raise ValueError("tenant_id must be a valid UUID") from exc


__all__ = ["coerce_conversation_uuid", "derive_conversation_key", "parse_tenant_id"]
