"""Actor context utilities shared between services and tools."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(slots=True)
class ConversationActorContext:
    tenant_id: str
    user_id: str


_ACTOR_CONTEXT: ContextVar[ConversationActorContext | None] = ContextVar(
    "conversation_actor_context",
    default=None,
)


def set_current_actor(actor: ConversationActorContext):
    """Push the active actor context and return the reset token."""

    return _ACTOR_CONTEXT.set(actor)


def reset_current_actor(token) -> None:
    """Reset the actor context using the provided token."""

    _ACTOR_CONTEXT.reset(token)


def get_current_actor() -> ConversationActorContext | None:
    """Return the actor bound to the current context, if any."""

    return _ACTOR_CONTEXT.get()


__all__ = [
    "ConversationActorContext",
    "get_current_actor",
    "reset_current_actor",
    "set_current_actor",
]
