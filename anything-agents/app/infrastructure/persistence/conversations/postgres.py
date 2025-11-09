"Postgres-backed conversation repository implementation."

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRecord,
    ConversationRepository,
    ConversationSessionState,
)
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
    TenantAccount,
)

logger = logging.getLogger("anything-agents.persistence")

_CONVERSATION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "anything-agents:conversation")
_MESSAGE_ROLES: tuple[str, ...] = ("user", "assistant", "system")


MessageRole = Literal["user", "assistant", "system"]


def _coerce_conversation_uuid(conversation_id: str) -> uuid.UUID:
    if not conversation_id:
        return uuid.uuid4()
    try:
        return uuid.UUID(conversation_id)
    except (TypeError, ValueError):
        return uuid.uuid5(_CONVERSATION_NAMESPACE, conversation_id)


def _derive_conversation_key(conversation_id: str) -> str:
    if not conversation_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(conversation_id))
    except (TypeError, ValueError):
        if len(conversation_id) > 255:
            raise ValueError(
                "Conversation identifier must be 255 characters or fewer."
            ) from None
        return conversation_id


class PostgresConversationRepository(ConversationRepository):
    """Persist conversations and messages using PostgreSQL."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        default_tenant_slug: str = "default",
        default_tenant_name: str = "Default Tenant",
    ) -> None:
        self._session_factory = session_factory
        self._default_tenant_slug = default_tenant_slug
        self._default_tenant_name = default_tenant_name

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        metadata: ConversationMetadata,
    ) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        conversation_key = _derive_conversation_key(conversation_id)
        async with self._session_factory() as session:
            tenant_id = await self._ensure_tenant(session, metadata.tenant_id)
            conversation = await self._get_or_create_conversation(
                session,
                conversation_uuid,
                conversation_key=conversation_key,
                tenant_id=tenant_id,
                metadata=metadata,
            )

            position = conversation.message_count
            conversation.message_count = position + 1
            conversation.last_message_at = _to_utc(message.timestamp)
            conversation.updated_at = datetime.now(UTC)
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
            if metadata.sdk_session_id:
                conversation.sdk_session_id = metadata.sdk_session_id
            if metadata.session_cursor:
                conversation.session_cursor = metadata.session_cursor
            if metadata.last_session_sync_at:
                conversation.last_session_sync_at = metadata.last_session_sync_at

            db_message = AgentMessage(
                conversation_id=conversation.id,
                position=position,
                role=message.role,
                agent_type=metadata.active_agent if message.role == "assistant" else None,
                content={"text": message.content},
                token_count_prompt=metadata.total_tokens_prompt
                if message.role == "assistant"
                else None,
                token_count_completion=metadata.total_tokens_completion
                if message.role == "assistant"
                else None,
                reasoning_tokens=metadata.reasoning_tokens if message.role == "assistant" else None,
                created_at=_to_utc(message.timestamp),
            )
            session.add(db_message)
            await session.commit()
            logger.debug(
                "Persisted %s message for conversation %s (agent=%s)",
                message.role,
                conversation_id,
                metadata.active_agent or metadata.agent_entrypoint,
            )

    async def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentMessage)
                .where(AgentMessage.conversation_id == conversation_uuid)
                .order_by(AgentMessage.position)
            )
            rows: Sequence[AgentMessage] = result.scalars().all()
            return [
                ConversationMessage(
                    role=_coerce_role(row.role),
                    content=_extract_message_content(row.content),
                    timestamp=row.created_at,
                )
                for row in rows
            ]

    async def list_conversation_ids(self) -> list[str]:
        async with self._session_factory() as session:
            result = await session.execute(select(AgentConversation.conversation_key))
            return [row[0] for row in result.all()]

    async def iter_conversations(self) -> list[ConversationRecord]:
        async with self._session_factory() as session:
            conversations = await session.execute(
                select(AgentConversation).order_by(AgentConversation.updated_at.desc())
            )
            conversation_rows: Sequence[AgentConversation] = conversations.scalars().all()
            if not conversation_rows:
                return []

            ids = [conversation.id for conversation in conversation_rows]
            messages = await session.execute(
                select(AgentMessage)
                .where(AgentMessage.conversation_id.in_(ids))
                .order_by(AgentMessage.conversation_id, AgentMessage.position)
            )
            message_rows: Sequence[AgentMessage] = messages.scalars().all()

            grouped: dict[uuid.UUID, list[AgentMessage]] = {}
            for row in message_rows:
                grouped.setdefault(row.conversation_id, []).append(row)

            records: list[ConversationRecord] = []
            for conversation in conversation_rows:
                entries = grouped.get(conversation.id, [])
                messages_list = [
                    ConversationMessage(
                        role=_coerce_role(item.role),
                        content=_extract_message_content(item.content),
                        timestamp=item.created_at,
                    )
                    for item in entries
                ]
                records.append(
                    ConversationRecord(
                        conversation_id=conversation.conversation_key,
                        messages=messages_list,
                    )
                )
            return records

    async def clear_conversation(self, conversation_id: str) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation:
                await session.delete(conversation)
                await session.commit()

    async def get_session_state(self, conversation_id: str) -> ConversationSessionState | None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None:
                return None
            return ConversationSessionState(
                sdk_session_id=conversation.sdk_session_id,
                session_cursor=conversation.session_cursor,
                last_session_sync_at=conversation.last_session_sync_at,
            )

    async def upsert_session_state(
        self, conversation_id: str, state: ConversationSessionState
    ) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        async with self._session_factory() as session:
            conversation = await session.get(
                AgentConversation, conversation_uuid, with_for_update=True
            )
            if conversation is None:
                raise ValueError(
                    f"Conversation {conversation_id} does not exist; "
                    "session state cannot be updated."
                )

            conversation.sdk_session_id = state.sdk_session_id
            conversation.session_cursor = state.session_cursor
            conversation.last_session_sync_at = state.last_session_sync_at

            await session.commit()

    async def _get_or_create_conversation(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        conversation_key: str,
        tenant_id: uuid.UUID,
        metadata: ConversationMetadata,
    ) -> AgentConversation:
        conversation = await session.get(
            AgentConversation,
            conversation_id,
            with_for_update=True,
        )
        if conversation:
            if conversation.conversation_key != conversation_key:
                conversation.conversation_key = conversation_key
            if metadata.sdk_session_id:
                conversation.sdk_session_id = metadata.sdk_session_id
            if metadata.session_cursor:
                conversation.session_cursor = metadata.session_cursor
            if metadata.last_session_sync_at:
                conversation.last_session_sync_at = metadata.last_session_sync_at
            return conversation

        conversation = AgentConversation(
            id=conversation_id,
            conversation_key=conversation_key,
            tenant_id=tenant_id,
            user_id=uuid.UUID(metadata.user_id) if metadata.user_id else None,
            agent_entrypoint=metadata.agent_entrypoint,
            active_agent=metadata.active_agent,
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

    async def _ensure_tenant(
        self,
        session: AsyncSession,
        tenant_id: str | None,
    ) -> uuid.UUID:
        if tenant_id:
            return uuid.UUID(tenant_id)

        result = await session.execute(
            select(TenantAccount).where(TenantAccount.slug == self._default_tenant_slug)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant.id

        tenant = TenantAccount(
            id=uuid.uuid4(),
            slug=self._default_tenant_slug,
            name=self._default_tenant_name,
            created_at=datetime.now(UTC),
        )
        session.add(tenant)
        try:
            await session.flush()
            logger.info("Created default tenant '%s'", self._default_tenant_slug)
        except IntegrityError:
            await session.rollback()
            existing = await session.execute(
                select(TenantAccount).where(TenantAccount.slug == self._default_tenant_slug)
            )
            tenant = existing.scalar_one()
        return tenant.id


def _extract_message_content(payload: dict | str | None) -> str:
    if isinstance(payload, dict):
        if "text" in payload:
            return str(payload["text"])
        return str(payload)
    if isinstance(payload, str):
        return payload
    return ""


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
def _coerce_role(value: str) -> MessageRole:
    if value not in _MESSAGE_ROLES:
        raise ValueError(f"Unsupported conversation role '{value}'")
    return cast(MessageRole, value)
