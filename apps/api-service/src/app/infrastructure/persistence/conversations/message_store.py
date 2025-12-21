"""Message persistence for conversations."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationNotFoundError,
    MessagePage,
    ensure_metadata_tenant,
)
from app.infrastructure.persistence.conversations.conversation_store import (
    ConversationStore,
    apply_message_metadata,
)
from app.infrastructure.persistence.conversations.cursors import (
    decode_message_cursor,
    encode_message_cursor,
)
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    derive_conversation_key,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_segments import (
    get_or_create_active_segment,
)
from app.infrastructure.persistence.conversations.ledger_visibility import (
    build_message_visibility_predicate,
    load_ledger_segments,
    load_ledger_segments_bulk,
)
from app.infrastructure.persistence.conversations.mappers import (
    message_from_row,
    serialize_attachments,
    to_utc,
)
from app.infrastructure.persistence.conversations.models import AgentMessage

logger = logging.getLogger("api-service.persistence")


class ConversationMessageStore:
    """Handles message CRUD for conversations."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        conversation_store: ConversationStore | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._conversations = conversation_store or ConversationStore(session_factory)

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> int | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        conversation_key = derive_conversation_key(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        ensure_metadata_tenant(metadata, tenant_id)
        async with self._session_factory() as session:
            conversation = await self._conversations.get_or_create_for_message(
                session,
                conversation_uuid,
                conversation_key=conversation_key,
                tenant_id=tenant_uuid,
                metadata=metadata,
            )
            segment = await get_or_create_active_segment(
                session,
                tenant_id=tenant_uuid,
                conversation_id=conversation.id,
            )

            position = conversation.message_count
            conversation.message_count = position + 1
            conversation.last_message_at = to_utc(message.timestamp)
            conversation.updated_at = datetime.now(UTC)
            apply_message_metadata(conversation, metadata=metadata)

            db_message = AgentMessage(
                conversation_id=conversation.id,
                segment_id=segment.id,
                position=position,
                role=message.role,
                agent_type=metadata.active_agent if message.role == "assistant" else None,
                content={"text": message.content},
                attachments=serialize_attachments(message.attachments),
                token_count_prompt=metadata.total_tokens_prompt
                if message.role == "assistant"
                else None,
                token_count_completion=metadata.total_tokens_completion
                if message.role == "assistant"
                else None,
                reasoning_tokens=metadata.reasoning_tokens if message.role == "assistant" else None,
                created_at=to_utc(message.timestamp),
            )
            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)
            logger.debug(
                "Persisted %s message for conversation %s (agent=%s)",
                message.role,
                conversation_id,
                metadata.active_agent or metadata.agent_entrypoint,
            )
            return getattr(db_message, "id", None)

    async def get_messages(
        self, conversation_id: str, *, tenant_id: str
    ) -> list[ConversationMessage]:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self._conversations.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            result = await session.execute(
                select(AgentMessage)
                .where(AgentMessage.conversation_id == conversation_uuid)
                .where(
                    build_message_visibility_predicate(
                        await load_ledger_segments(
                            session,
                            tenant_id=tenant_uuid,
                            conversation_id=conversation_uuid,
                        )
                    )
                )
                .order_by(AgentMessage.position)
            )
            rows: Sequence[AgentMessage] = result.scalars().all()
            return [message_from_row(row) for row in rows]

    async def paginate_messages(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        direction: str = "desc",
    ) -> MessagePage:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        limit = max(1, min(limit, 100))
        direction_normalized = (direction or "desc").lower()
        if direction_normalized not in ("asc", "desc"):
            raise ValueError("direction must be 'asc' or 'desc'")

        cursor_ts: datetime | None = None
        cursor_id: int | None = None
        if cursor:
            cursor_ts, cursor_id = decode_message_cursor(cursor)
            cursor_ts = to_utc(cursor_ts)

        async with self._session_factory() as session:
            conversation = await self._conversations.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            stmt = select(AgentMessage).where(AgentMessage.conversation_id == conversation_uuid)
            stmt = stmt.where(
                build_message_visibility_predicate(
                    await load_ledger_segments(
                        session,
                        tenant_id=tenant_uuid,
                        conversation_id=conversation_uuid,
                    )
                )
            )

            if cursor_ts and cursor_id is not None:
                if direction_normalized == "desc":
                    stmt = stmt.where(
                        or_(
                            AgentMessage.created_at < cursor_ts,
                            and_(
                                AgentMessage.created_at == cursor_ts,
                                AgentMessage.id < cursor_id,
                            ),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            AgentMessage.created_at > cursor_ts,
                            and_(
                                AgentMessage.created_at == cursor_ts,
                                AgentMessage.id > cursor_id,
                            ),
                        )
                    )

            if direction_normalized == "desc":
                stmt = stmt.order_by(
                    AgentMessage.created_at.desc(),
                    AgentMessage.id.desc(),
                )
            else:
                stmt = stmt.order_by(
                    AgentMessage.created_at.asc(),
                    AgentMessage.id.asc(),
                )

            stmt = stmt.limit(limit + 1)

            result = await session.execute(stmt)
            rows: Sequence[AgentMessage] = result.scalars().all()

            has_extra = len(rows) > limit
            rows = rows[:limit]

            messages = [message_from_row(row) for row in rows]

            next_cursor = None
            if has_extra and rows:
                tail = rows[-1]
                next_cursor = encode_message_cursor(tail.created_at, tail.id)

            return MessagePage(items=messages, next_cursor=next_cursor)

    async def load_messages_for_conversations(
        self,
        session: AsyncSession,
        *,
        conversation_ids: list[uuid.UUID],
        tenant_id: uuid.UUID,
    ) -> dict[uuid.UUID, list[AgentMessage]]:
        if not conversation_ids:
            return {}
        segments = await load_ledger_segments_bulk(
            session,
            tenant_id=tenant_id,
            conversation_ids=conversation_ids,
        )
        visibility_predicate = build_message_visibility_predicate(segments)
        messages = await session.execute(
            select(AgentMessage)
            .where(
                AgentMessage.conversation_id.in_(conversation_ids),
                visibility_predicate,
            )
            .order_by(AgentMessage.conversation_id, AgentMessage.position)
        )
        rows: Sequence[AgentMessage] = messages.scalars().all()
        grouped: dict[uuid.UUID, list[AgentMessage]] = {}
        for row in rows:
            grouped.setdefault(row.conversation_id, []).append(row)
        return grouped


__all__ = ["ConversationMessageStore"]
