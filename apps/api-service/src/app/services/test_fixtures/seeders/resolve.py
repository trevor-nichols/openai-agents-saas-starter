"""Resolve references between fixture records."""

from __future__ import annotations

from uuid import UUID

from app.services.test_fixtures.errors import TestFixtureError
from app.services.test_fixtures.schemas import (
    FixtureConversationResult,
    FixtureUserResult,
)


def resolve_user_id(
    email: str | None, user_results: dict[str, FixtureUserResult]
) -> UUID | None:
    if email is None:
        return None
    entry = user_results.get(email)
    if entry is None:
        raise TestFixtureError(f"Conversation references unknown user '{email}'.")
    return UUID(entry.user_id)


def resolve_conversation_id(
    key: str | None, conversation_results: dict[str, FixtureConversationResult]
) -> UUID | None:
    if key is None:
        return None
    entry = conversation_results.get(key)
    if entry is None:
        raise TestFixtureError(f"Asset references unknown conversation '{key}'.")
    return UUID(entry.conversation_id)


__all__ = ["resolve_conversation_id", "resolve_user_id"]
