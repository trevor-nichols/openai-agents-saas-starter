"""Postgres-backed conversation repository composition root."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationEvent,
    ConversationMessage,
    ConversationMetadata,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationSearchPage,
    ConversationSessionState,
)
from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore
from app.infrastructure.persistence.conversations.run_event_store import RunEventStore
from app.infrastructure.persistence.conversations.search_store import ConversationSearchStore


class PostgresConversationRepository(ConversationRepository):
    """Facade that delegates to focused stores for each capability."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._messages = ConversationMessageStore(session_factory)
        self._search = ConversationSearchStore(session_factory)
        self._run_events = RunEventStore(session_factory)

    # --- messages / conversations ------------------------------------
    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> None:
        await self._messages.add_message(
            conversation_id, message, tenant_id=tenant_id, metadata=metadata
        )

    async def get_messages(
        self, conversation_id: str, *, tenant_id: str
    ) -> list[ConversationMessage]:
        return await self._messages.get_messages(conversation_id, tenant_id=tenant_id)

    async def get_conversation(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationRecord | None:
        return await self._messages.get_conversation(conversation_id, tenant_id=tenant_id)

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        return await self._messages.list_conversation_ids(tenant_id=tenant_id)

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]:
        return await self._messages.iter_conversations(tenant_id=tenant_id)

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage:
        return await self._messages.paginate_conversations(
            tenant_id=tenant_id,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

    async def paginate_messages(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        direction: str = "desc",
    ):
        return await self._messages.paginate_messages(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            limit=limit,
            cursor=cursor,
            direction=direction,
        )

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        await self._messages.clear_conversation(conversation_id, tenant_id=tenant_id)

    async def get_session_state(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationSessionState | None:
        return await self._messages.get_session_state(conversation_id, tenant_id=tenant_id)

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        await self._messages.upsert_session_state(conversation_id, tenant_id=tenant_id, state=state)

    # --- search -------------------------------------------------------
    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage:
        return await self._search.search_conversations(
            tenant_id=tenant_id,
            query=query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )

    # --- run events ---------------------------------------------------
    async def add_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationEvent],
    ) -> None:
        await self._run_events.add_run_events(conversation_id, tenant_id=tenant_id, events=events)

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        return await self._run_events.get_run_events(
            conversation_id,
            tenant_id=tenant_id,
            workflow_run_id=workflow_run_id,
        )


__all__ = ["PostgresConversationRepository"]
