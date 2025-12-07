"""Persistence for cross-session conversation summaries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import ConversationNotFoundError
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    ConversationSummary,
)


class ConversationSummaryStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def persist_summary(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        agent_key: str | None,
        summary_text: str,
        summary_model: str | None = None,
        summary_length_tokens: int | None = None,
        expires_at: datetime | None = None,
        version: str | None = None,
    ) -> None:
        if not summary_text:
            return
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")
            row = ConversationSummary(
                tenant_id=tenant_uuid,
                conversation_id=conversation_uuid,
                agent_key=agent_key,
                summary_text=summary_text,
                summary_model=summary_model,
                summary_length_tokens=summary_length_tokens,
                expires_at=expires_at,
                version=version,
                created_at=datetime.now(UTC),
            )
            session.add(row)
            await session.commit()

    async def get_latest_summary(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        agent_key: str | None,
        max_age_seconds: int | None = None,
    ) -> ConversationSummary | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        cutoff = None
        if max_age_seconds is not None:
            cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)

        async with self._session_factory() as session:
            stmt = select(ConversationSummary).where(
                ConversationSummary.tenant_id == tenant_uuid,
                ConversationSummary.conversation_id == conversation_uuid,
            )
            if agent_key:
                stmt = stmt.where(ConversationSummary.agent_key == agent_key)
            if cutoff:
                stmt = stmt.where(ConversationSummary.created_at >= cutoff)

            stmt = stmt.order_by(ConversationSummary.created_at.desc())
            result = await session.execute(stmt)
            row = result.scalars().first()
            return row


__all__ = ["ConversationSummaryStore"]
