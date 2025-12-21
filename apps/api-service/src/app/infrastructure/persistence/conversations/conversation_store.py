"""Conversation row persistence helpers."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationMemoryConfig,
    ConversationMetadata,
    ConversationNotFoundError,
    ConversationSessionState,
)
from app.infrastructure.persistence.conversations.cursors import (
    decode_list_cursor,
    encode_list_cursor,
)
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.mappers import to_utc
from app.infrastructure.persistence.conversations.models import AgentConversation

logger = logging.getLogger("api-service.persistence")


class ConversationStore:
    """Persistence adapter for conversation rows and metadata."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_conversation_row(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        strict: bool = True,
    ) -> AgentConversation | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            return await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=strict,
            )

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConversation.conversation_key).where(
                    AgentConversation.tenant_id == tenant_uuid
                )
            )
            return [row[0] for row in result.all()]

    async def list_conversation_rows(self, *, tenant_id: str) -> list[AgentConversation]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            return await self.list_conversation_rows_in_session(
                session,
                tenant_id=tenant_uuid,
            )

    async def paginate_conversation_rows(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> tuple[list[AgentConversation], str | None]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            return await self.paginate_conversation_rows_in_session(
                session,
                tenant_id=tenant_uuid,
                limit=limit,
                cursor=cursor,
                agent_entrypoint=agent_entrypoint,
                updated_after=updated_after,
            )

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                for_update=True,
            )
            if conversation:
                await session.delete(conversation)
                await session.commit()

    async def get_session_state(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationSessionState | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
            )
            if conversation is None:
                return None
            return ConversationSessionState(
                provider=conversation.provider,
                provider_conversation_id=conversation.provider_conversation_id,
                sdk_session_id=conversation.sdk_session_id,
                session_cursor=conversation.session_cursor,
                last_session_sync_at=conversation.last_session_sync_at,
            )

    async def get_memory_config(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationMemoryConfig | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
            )
            if conversation is None:
                return None
            return ConversationMemoryConfig(
                strategy=conversation.memory_strategy,
                max_user_turns=conversation.memory_max_turns,
                keep_last_turns=conversation.memory_keep_last_turns,
                compact_trigger_turns=conversation.memory_compact_trigger_turns,
                compact_keep=conversation.memory_compact_keep,
                clear_tool_inputs=conversation.memory_clear_tool_inputs,
                memory_injection=conversation.memory_injection,
            )

    async def set_memory_config(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        config: ConversationMemoryConfig,
        provided_fields: set[str] | None = None,
    ) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                for_update=True,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            fields = provided_fields or set()

            if "mode" in fields:
                conversation.memory_strategy = config.strategy[:16] if config.strategy else None
            if "max_user_turns" in fields:
                conversation.memory_max_turns = config.max_user_turns
            if "keep_last_turns" in fields:
                conversation.memory_keep_last_turns = config.keep_last_turns
            if "compact_trigger_turns" in fields:
                conversation.memory_compact_trigger_turns = config.compact_trigger_turns
            if "compact_keep" in fields:
                conversation.memory_compact_keep = config.compact_keep
            if "clear_tool_inputs" in fields:
                conversation.memory_clear_tool_inputs = (
                    bool(config.clear_tool_inputs)
                    if config.clear_tool_inputs is not None
                    else None
                )
            if "memory_injection" in fields:
                conversation.memory_injection = (
                    bool(config.memory_injection)
                    if config.memory_injection is not None
                    else None
                )
            conversation.updated_at = datetime.now(UTC)
            await session.commit()

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                for_update=True,
                strict=True,
            )
            if conversation is None:
                raise ValueError(
                    f"Conversation {conversation_id} does not exist; "
                    "session state cannot be updated."
                )

            conversation.sdk_session_id = state.sdk_session_id
            conversation.session_cursor = state.session_cursor
            conversation.last_session_sync_at = state.last_session_sync_at
            conversation.provider = state.provider or conversation.provider
            if state.provider_conversation_id:
                conversation.provider_conversation_id = state.provider_conversation_id

            await session.commit()

    async def set_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
        generated_at: datetime | None = None,
    ) -> bool:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                for_update=True,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")
            if conversation.display_name:
                return False

            conversation.display_name = display_name[:128]
            conversation.title_generated_at = generated_at or datetime.now(UTC)
            conversation.updated_at = datetime.now(UTC)
            await session.commit()
            return True

    async def update_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
    ) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        normalized = (display_name or "").strip()
        if not normalized:
            raise ValueError("display_name is required")

        async with self._session_factory() as session:
            conversation = await self.get_conversation_row_in_session(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                for_update=True,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            conversation.display_name = normalized[:128]
            conversation.updated_at = datetime.now(UTC)
            await session.commit()

    async def get_or_create_for_message(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        conversation_key: str,
        tenant_id: uuid.UUID,
        metadata: ConversationMetadata,
    ) -> AgentConversation:
        conversation = await self.get_conversation_row_in_session(
            session,
            conversation_id,
            tenant_id=tenant_id,
            for_update=True,
            strict=True,
        )
        if conversation:
            if conversation.conversation_key != conversation_key:
                conversation.conversation_key = conversation_key
            return conversation

        conversation = AgentConversation(
            id=conversation_id,
            conversation_key=conversation_key,
            tenant_id=tenant_id,
            user_id=uuid.UUID(metadata.user_id) if metadata.user_id else None,
            agent_entrypoint=metadata.agent_entrypoint,
            active_agent=metadata.active_agent,
            provider=metadata.provider,
            provider_conversation_id=metadata.provider_conversation_id,
            source_channel=metadata.source_channel,
            topic_hint=metadata.topic_hint,
            message_count=0,
            total_tokens_prompt=metadata.total_tokens_prompt or 0,
            total_tokens_completion=metadata.total_tokens_completion or 0,
            reasoning_tokens=metadata.reasoning_tokens or 0,
            handoff_count=metadata.handoff_count or 0,
            sdk_session_id=metadata.sdk_session_id,
            session_cursor=metadata.session_cursor,
            last_session_sync_at=metadata.last_session_sync_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        return conversation

    async def list_conversation_rows_in_session(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
    ) -> list[AgentConversation]:
        conversations = await session.execute(
            select(AgentConversation)
            .where(AgentConversation.tenant_id == tenant_id)
            .order_by(AgentConversation.updated_at.desc())
        )
        conversation_rows: Sequence[AgentConversation] = conversations.scalars().all()
        return list(conversation_rows)

    async def paginate_conversation_rows_in_session(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> tuple[list[AgentConversation], str | None]:
        limit = max(1, min(limit, 100))

        cursor_ts: datetime | None = None
        cursor_uuid: uuid.UUID | None = None
        if cursor:
            cursor_ts, cursor_uuid = decode_list_cursor(cursor)

        filters = [AgentConversation.tenant_id == tenant_id]
        if agent_entrypoint:
            filters.append(AgentConversation.agent_entrypoint == agent_entrypoint)
        if updated_after:
            filters.append(AgentConversation.updated_at >= to_utc(updated_after))
        if cursor_ts and cursor_uuid:
            filters.append(
                or_(
                    AgentConversation.updated_at < cursor_ts,
                    and_(
                        AgentConversation.updated_at == cursor_ts,
                        AgentConversation.id < cursor_uuid,
                    ),
                )
            )

        result = await session.execute(
            select(AgentConversation)
            .where(*filters)
            .order_by(AgentConversation.updated_at.desc(), AgentConversation.id.desc())
            .limit(limit + 1)
        )
        rows: list[AgentConversation] = list(result.scalars().all())

        next_cursor = None
        if len(rows) > limit:
            tail = rows[limit]
            next_cursor = encode_list_cursor(tail.updated_at, tail.id)
            rows = rows[:limit]

        return rows, next_cursor

    async def get_conversation_row_in_session(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        for_update: bool = False,
        strict: bool = False,
    ) -> AgentConversation | None:
        conversation = await session.get(
            AgentConversation,
            conversation_id,
            with_for_update=for_update,
        )
        if conversation is None:
            return None
        if conversation.tenant_id != tenant_id:
            logger.warning(
                "Conversation %s accessed with mismatched tenant (expected=%s, actual=%s)",
                conversation_id,
                tenant_id,
                conversation.tenant_id,
            )
            if strict:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} does not exist"
                )
            return None
        return conversation


def apply_message_metadata(
    conversation: AgentConversation, *, metadata: ConversationMetadata
) -> None:
    conversation.agent_entrypoint = metadata.agent_entrypoint
    if metadata.active_agent:
        conversation.active_agent = metadata.active_agent
    if metadata.topic_hint:
        conversation.topic_hint = metadata.topic_hint
    if metadata.source_channel:
        conversation.source_channel = metadata.source_channel
    if metadata.handoff_count is not None:
        conversation.handoff_count = metadata.handoff_count
    if metadata.total_tokens_prompt is not None:
        conversation.total_tokens_prompt = metadata.total_tokens_prompt
    if metadata.total_tokens_completion is not None:
        conversation.total_tokens_completion = metadata.total_tokens_completion
    if metadata.reasoning_tokens is not None:
        conversation.reasoning_tokens = metadata.reasoning_tokens
    if metadata.provider:
        conversation.provider = metadata.provider
    if metadata.provider_conversation_id:
        conversation.provider_conversation_id = metadata.provider_conversation_id
    if metadata.sdk_session_id:
        conversation.sdk_session_id = metadata.sdk_session_id
    if metadata.session_cursor:
        conversation.session_cursor = metadata.session_cursor
    if metadata.last_session_sync_at:
        conversation.last_session_sync_at = metadata.last_session_sync_at


__all__ = ["ConversationStore", "apply_message_metadata"]
