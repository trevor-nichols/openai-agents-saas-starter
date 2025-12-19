"""Conversation truncation (per-message deletion) service.

User-facing semantics:
- Users can delete only *user* messages.
- Deleting a user message truncates the visible conversation line at that message,
  removing the message and all subsequent content (messages + tools + checkpoints).
- Physical deletion of the truncated suffix is handled later by background GC.

Implementation strategy:
- Use `conversation_ledger_segments` to model the visible lineage.
- Mark the segment containing the deleted message as truncated with visibility cutoffs:
  - `visible_through_message_position = deleted.position - 1`
  - `visible_through_event_id = last ledger event before deleted.created_at`
- Hide any later segments entirely (superseded history) by setting their visibility cutoffs
  to an empty range.
- Create a new active segment so future runs append into a clean lineage.
- Reset the Agents SDK SQLAlchemy session by rebuilding it from the remaining visible
  messages (best-effort). Also clear stored summaries to avoid leaking deleted context.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from agents.items import TResponseInputItem
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationMessageNotDeletableError,
    ConversationMessageNotFoundError,
    ConversationNotFoundError,
)
from app.infrastructure.db.engine import get_engine
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
    ConversationSummary,
)
from app.infrastructure.providers.openai.session_store import (
    SESSION_MESSAGES_TABLE_NAME,
    SESSION_TABLE_NAME,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ConversationTruncationResult:
    conversation_id: str
    deleted_message_id: str


class ConversationTruncationService:
    """Coordinates per-message deletion across message history, ledger, and memory state."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def truncate_from_user_message(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        actor_user_id: str,
        message_id: str,
    ) -> ConversationTruncationResult:
        """Truncate the visible conversation line from a user message (inclusive)."""

        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)

        try:
            message_pk = int(message_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("message_id must be an integer string") from exc
        if message_pk <= 0:
            raise ValueError("message_id must be a positive integer")

        remaining_messages: list[TResponseInputItem] = []
        sdk_session_id: str | None = None

        async with self._session_factory() as session:
            async with session.begin():
                conversation = await session.get(
                    AgentConversation,
                    conversation_uuid,
                    with_for_update=True,
                )
                if conversation is None or conversation.tenant_id != tenant_uuid:
                    raise ConversationNotFoundError(
                        f"Conversation {conversation_id} does not exist"
                    )

                _ensure_actor_is_owner(actor_user_id, conversation)

                message = await session.scalar(
                    select(AgentMessage).where(
                        AgentMessage.id == message_pk,
                        AgentMessage.conversation_id == conversation_uuid,
                    )
                )
                if message is None:
                    raise ConversationMessageNotFoundError(
                        f"Message {message_id} does not exist in conversation {conversation_id}"
                    )

                if (message.role or "").lower() != "user":
                    raise ConversationMessageNotDeletableError(
                        "Only user messages can be deleted"
                    )

                segment = await session.get(ConversationLedgerSegment, message.segment_id)
                if segment is None:
                    raise RuntimeError("Message segment does not exist")  # pragma: no cover
                if segment.conversation_id != conversation_uuid:
                    raise RuntimeError("Message segment mismatch")  # pragma: no cover

                # Validate the message is currently visible.
                # (Cannot delete already-truncated content.)
                if segment.truncated_at is not None:
                    max_pos = segment.visible_through_message_position
                    if max_pos is None or int(message.position) > int(max_pos):
                        raise ConversationMessageNotDeletableError(
                            "Message is not visible in the current conversation lineage"
                        )

                segments = await _load_segments_for_update(
                    session,
                    tenant_id=tenant_uuid,
                    conversation_id=conversation_uuid,
                )

                now = datetime.now(UTC)

                # Determine the last visible ledger event in this segment,
                # prior to the deleted message.
                max_event_id = await session.scalar(
                    select(func.max(ConversationLedgerEvent.id)).where(
                        ConversationLedgerEvent.tenant_id == tenant_uuid,
                        ConversationLedgerEvent.conversation_id == conversation_uuid,
                        ConversationLedgerEvent.segment_id == segment.id,
                        ConversationLedgerEvent.server_timestamp < message.created_at,
                    )
                )
                segment.visible_through_event_id = int(max_event_id) if max_event_id else 0
                segment.visible_through_message_position = int(message.position) - 1
                segment.truncated_at = now
                segment.updated_at = now

                # Supersede any later segments entirely.
                # (They represent history "after" the deleted message.)
                for seg in segments:
                    if seg.segment_index <= segment.segment_index:
                        continue
                    seg.visible_through_event_id = 0
                    seg.visible_through_message_position = -1
                    seg.truncated_at = now
                    seg.updated_at = now

                # Create a new active segment so future runs append to a clean lineage.
                max_index = max((int(seg.segment_index) for seg in segments), default=-1)
                new_segment = ConversationLedgerSegment(
                    tenant_id=tenant_uuid,
                    conversation_id=conversation_uuid,
                    segment_index=max_index + 1,
                    parent_segment_id=segment.id,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_segment)
                await session.flush()

                # Clear any summaries since they may contain content that is now truncated.
                await session.execute(
                    delete(ConversationSummary).where(
                        ConversationSummary.tenant_id == tenant_uuid,
                        ConversationSummary.conversation_id == conversation_uuid,
                    )
                )

                # Capture the remaining visible messages for rebuilding the SDK session,
                # after commit.
                remaining_messages = await _load_visible_session_messages(
                    session,
                    tenant_id=tenant_uuid,
                    conversation_id=conversation_uuid,
                )
                sdk_session_id = (
                    conversation.sdk_session_id
                    or conversation.provider_conversation_id
                    or conversation.conversation_key
                )

        # Best-effort: rebuild the provider session store to avoid leaking deleted context.
        if sdk_session_id and remaining_messages:
            await _rebuild_sqlalchemy_session(
                session_id=sdk_session_id,
                items=remaining_messages,
            )
        elif sdk_session_id:
            await _rebuild_sqlalchemy_session(session_id=sdk_session_id, items=[])

        return ConversationTruncationResult(
            conversation_id=conversation_id,
            deleted_message_id=message_id,
        )


def _ensure_actor_is_owner(actor_user_id: str, conversation: AgentConversation) -> None:
    """Enforce per-message deletion ownership semantics.

    We don't currently persist per-message author ids; conversations are user-scoped.
    """

    if conversation.user_id is None:
        return
    try:
        actor_uuid = uuid.UUID(actor_user_id)
    except (TypeError, ValueError) as exc:
        raise PermissionError("User is not permitted to modify this conversation") from exc
    if actor_uuid != conversation.user_id:
        raise PermissionError("User is not permitted to modify this conversation")


async def _load_segments_for_update(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[ConversationLedgerSegment]:
    result = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id == conversation_id,
        )
        .order_by(ConversationLedgerSegment.segment_index.asc())
    )
    return list(result.scalars().all())


async def _load_visible_session_messages(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[TResponseInputItem]:
    """Return visible message items in Agents SDK session format (message-only)."""

    # Visibility clause: active segment includes all; truncated segments include only prefix.
    visibility = func.coalesce(ConversationLedgerSegment.visible_through_message_position, -1)
    result = await session.execute(
        select(AgentMessage)
        .join(
            ConversationLedgerSegment,
            ConversationLedgerSegment.id == AgentMessage.segment_id,
        )
        .where(
            AgentMessage.conversation_id == conversation_id,
            ConversationLedgerSegment.tenant_id == tenant_id,
            or_(
                ConversationLedgerSegment.truncated_at.is_(None),
                AgentMessage.position <= visibility,
            ),
        )
        .order_by(AgentMessage.position.asc(), AgentMessage.id.asc())
    )

    rows = list(result.scalars().all())
    items: list[TResponseInputItem] = []
    for row in rows:
        role = (row.role or "").lower()
        if role not in {"user", "assistant", "system"}:
            continue
        items.append(
            cast(
                TResponseInputItem,
                {
                    "type": "message",
                    "role": role,
                    "content": row.content.get("text")
                    if isinstance(row.content, dict) and "text" in row.content
                    else str(row.content),
                },
            )
        )
    return items


async def _rebuild_sqlalchemy_session(
    *, session_id: str, items: list[TResponseInputItem]
) -> None:
    engine = get_engine()
    if engine is None:
        logger.warning(
            "truncate.rebuild_session_skipped_no_engine",
            extra={"session_id": session_id},
        )
        return

    handle: SQLAlchemySession = SQLAlchemySession(
        session_id=session_id,
        engine=engine,
        create_tables=engine.dialect.name.startswith("sqlite"),
        sessions_table=SESSION_TABLE_NAME,
        messages_table=SESSION_MESSAGES_TABLE_NAME,
    )

    try:
        await handle.clear_session()
        if items:
            await handle.add_items(items)
    except Exception:  # pragma: no cover - best effort
        logger.exception("truncate.rebuild_session_failed", extra={"session_id": session_id})


def get_conversation_truncation_service() -> ConversationTruncationService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()

    # Cache the service in the container for consistency with other service factories.
    svc = getattr(container, "conversation_truncation_service", None)
    if svc is None:
        svc = ConversationTruncationService(container.session_factory)
        container.conversation_truncation_service = svc
    return svc


__all__ = [
    "ConversationTruncationResult",
    "ConversationTruncationService",
    "get_conversation_truncation_service",
]
