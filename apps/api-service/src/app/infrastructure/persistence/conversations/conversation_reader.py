"""Conversation read-model assembly helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import ConversationPage, ConversationRecord
from app.infrastructure.persistence.conversations.conversation_store import ConversationStore
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.mappers import record_from_model
from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore


class ConversationReader:
    """Composes conversations + messages into domain records."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._conversations = ConversationStore(session_factory)
        self._messages = ConversationMessageStore(
            session_factory, conversation_store=self._conversations
        )

    async def get_conversation(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationRecord | None:
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
                return None

            messages = await self._messages.load_messages_for_conversations(
                session,
                conversation_ids=[conversation.id],
                tenant_id=tenant_uuid,
            )
            return record_from_model(conversation, messages.get(conversation.id, []))

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation_rows = await self._conversations.list_conversation_rows_in_session(
                session,
                tenant_id=tenant_uuid,
            )
            if not conversation_rows:
                return []

            messages = await self._messages.load_messages_for_conversations(
                session,
                conversation_ids=[conversation.id for conversation in conversation_rows],
                tenant_id=tenant_uuid,
            )
            return [
                record_from_model(conversation, messages.get(conversation.id, []))
                for conversation in conversation_rows
            ]

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            rows, next_cursor = await self._conversations.paginate_conversation_rows_in_session(
                session,
                tenant_id=tenant_uuid,
                limit=limit,
                cursor=cursor,
                agent_entrypoint=agent_entrypoint,
                updated_after=updated_after,
            )

            if not rows:
                return ConversationPage(items=[], next_cursor=None)

            messages = await self._messages.load_messages_for_conversations(
                session,
                conversation_ids=[conversation.id for conversation in rows],
                tenant_id=tenant_uuid,
            )
            records = [
                record_from_model(conversation, messages.get(conversation.id, []))
                for conversation in rows
            ]
            return ConversationPage(items=records, next_cursor=next_cursor)


__all__ = ["ConversationReader"]
