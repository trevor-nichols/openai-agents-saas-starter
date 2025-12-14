"""Postgres-backed conversation repository composition root."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationEvent,
    ConversationMemoryConfig,
    ConversationMessage,
    ConversationMetadata,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationRunUsage,
    ConversationSearchPage,
    ConversationSessionState,
)
from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore
from app.infrastructure.persistence.conversations.run_event_store import RunEventStore
from app.infrastructure.persistence.conversations.search_store import ConversationSearchStore
from app.infrastructure.persistence.conversations.summary_store import ConversationSummaryStore
from app.infrastructure.persistence.conversations.usage_store import RunUsageStore


class PostgresConversationRepository(ConversationRepository):
    """Facade that delegates to focused stores for each capability."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._messages = ConversationMessageStore(session_factory)
        self._search = ConversationSearchStore(session_factory)
        self._run_events = RunEventStore(session_factory)
        self._summaries = ConversationSummaryStore(session_factory)
        self._run_usage = RunUsageStore(session_factory)

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

    async def get_memory_config(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationMemoryConfig | None:
        return await self._messages.get_memory_config(conversation_id, tenant_id=tenant_id)

    async def set_memory_config(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        config: ConversationMemoryConfig,
        provided_fields: set[str] | None = None,
    ) -> None:
        await self._messages.set_memory_config(
            conversation_id, tenant_id=tenant_id, config=config, provided_fields=provided_fields
        )

    # --- summaries -------------------------------------------------------
    async def persist_summary(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_key: str | None,
        summary_text: str,
        summary_model: str | None = None,
        summary_length_tokens: int | None = None,
        version: str | None = None,
    ) -> None:
        await self._summaries.persist_summary(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            agent_key=agent_key,
            summary_text=summary_text,
            summary_model=summary_model,
            summary_length_tokens=summary_length_tokens,
            version=version,
        )

    async def get_latest_summary(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_key: str | None,
        max_age_seconds: int | None = None,
    ):
        return await self._summaries.get_latest_summary(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            agent_key=agent_key,
            max_age_seconds=max_age_seconds,
        )

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        await self._messages.upsert_session_state(conversation_id, tenant_id=tenant_id, state=state)

    async def add_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        usage: ConversationRunUsage,
    ) -> None:
        await self._run_usage.add_run_usage(conversation_id, tenant_id=tenant_id, usage=usage)

    async def list_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int = 20,
    ) -> list[ConversationRunUsage]:
        return await self._run_usage.list_run_usage(
            conversation_id, tenant_id=tenant_id, limit=limit
        )

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

    async def set_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
        generated_at: datetime | None = None,
    ) -> bool:
        return await self._messages.set_display_name(
            conversation_id,
            tenant_id=tenant_id,
            display_name=display_name,
            generated_at=generated_at,
        )

    async def update_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
    ) -> None:
        await self._messages.update_display_name(
            conversation_id,
            tenant_id=tenant_id,
            display_name=display_name,
        )


__all__ = ["PostgresConversationRepository"]
