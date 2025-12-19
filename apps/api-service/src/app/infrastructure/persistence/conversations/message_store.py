"""Conversation/message persistence primitives."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationMemoryConfig,
    ConversationMessage,
    ConversationMetadata,
    ConversationNotFoundError,
    ConversationPage,
    ConversationRecord,
    ConversationSessionState,
    MessagePage,
)
from app.infrastructure.persistence.conversations.cursors import (
    decode_list_cursor,
    decode_message_cursor,
    encode_list_cursor,
    encode_message_cursor,
)
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    derive_conversation_key,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.ledger_segments import (
    get_or_create_active_segment,
)
from app.infrastructure.persistence.conversations.mappers import (
    coerce_role,
    extract_attachments,
    extract_message_content,
    record_from_model,
    serialize_attachments,
    to_utc,
)
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage

logger = logging.getLogger("api-service.persistence")


class ConversationMessageStore:
    """Handles conversation + message CRUD without search or run events."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
        _ensure_metadata_tenant(metadata, tenant_id)
        async with self._session_factory() as session:
            conversation = await self._get_or_create_conversation(
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
            conversation = await self._get_conversation(
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
                    _message_visibility_predicate(
                        await _load_ledger_segments(
                            session,
                            tenant_id=tenant_uuid,
                            conversation_id=conversation_uuid,
                        )
                    )
                )
                .order_by(AgentMessage.position)
            )
            rows: Sequence[AgentMessage] = result.scalars().all()
            return [
                ConversationMessage(
                    message_id=str(row.id) if row.id is not None else None,
                    position=int(row.position) if row.position is not None else None,
                    role=coerce_role(row.role),
                    content=extract_message_content(row.content),
                    attachments=extract_attachments(row.attachments),
                    timestamp=row.created_at,
                )
                for row in rows
            ]

    async def get_conversation(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationRecord | None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self._get_conversation(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=True,
            )
            if conversation is None:
                return None

            messages = await self._load_messages(
                session,
                [conversation.id],
                tenant_id=tenant_uuid,
            )
            grouped = {conversation.id: messages.get(conversation.id, [])}
            return record_from_model(conversation, grouped.get(conversation.id, []))

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConversation.conversation_key).where(
                    AgentConversation.tenant_id == tenant_uuid
                )
            )
            return [row[0] for row in result.all()]

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]:
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversations = await session.execute(
                select(AgentConversation)
                .where(AgentConversation.tenant_id == tenant_uuid)
                .order_by(AgentConversation.updated_at.desc())
            )
            conversation_rows: Sequence[AgentConversation] = conversations.scalars().all()
            if not conversation_rows:
                return []

            grouped = await self._load_messages(
                session,
                [conversation.id for conversation in conversation_rows],
                tenant_id=tenant_uuid,
            )
            return [
                record_from_model(conversation, grouped.get(conversation.id, []))
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
        limit = max(1, min(limit, 100))

        cursor_ts: datetime | None = None
        cursor_uuid: uuid.UUID | None = None
        if cursor:
            cursor_ts, cursor_uuid = decode_list_cursor(cursor)

        filters = [AgentConversation.tenant_id == tenant_uuid]
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

        async with self._session_factory() as session:
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

            if not rows:
                return ConversationPage(items=[], next_cursor=None)

            grouped = await self._load_messages(
                session,
                [conversation.id for conversation in rows],
                tenant_id=tenant_uuid,
            )
            records = [
                record_from_model(conversation, grouped.get(conversation.id, []))
                for conversation in rows
            ]
            return ConversationPage(items=records, next_cursor=next_cursor)

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
            conversation = await self._get_conversation(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=True,
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            stmt = select(AgentMessage).where(AgentMessage.conversation_id == conversation_uuid)
            stmt = stmt.where(
                _message_visibility_predicate(
                    await _load_ledger_segments(
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

            messages = [
                ConversationMessage(
                    message_id=str(row.id) if row.id is not None else None,
                    position=int(row.position) if row.position is not None else None,
                    role=coerce_role(row.role),
                    content=extract_message_content(row.content),
                    attachments=extract_attachments(row.attachments),
                    timestamp=row.created_at,
                )
                for row in rows
            ]

            next_cursor = None
            if has_extra and rows:
                tail = rows[-1]
                next_cursor = encode_message_cursor(tail.created_at, tail.id)

            return MessagePage(items=messages, next_cursor=next_cursor)

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await self._get_conversation(
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
            conversation = await self._get_conversation(
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
            conversation = await self._get_conversation(
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
            conversation = await self._get_conversation(
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
                conversation.memory_strategy = (config.strategy[:16] if config.strategy else None)
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
            conversation = await self._get_conversation(
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
            conversation = await self._get_conversation(
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
            conversation = await self._get_conversation(
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

    # --- internals -----------------------------------------------------
    async def _get_or_create_conversation(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        conversation_key: str,
        tenant_id: uuid.UUID,
        metadata: ConversationMetadata,
    ) -> AgentConversation:
        conversation = await self._get_conversation(
            session,
            conversation_id,
            tenant_id=tenant_id,
            for_update=True,
            strict=True,
        )
        if conversation:
            if conversation.conversation_key != conversation_key:
                conversation.conversation_key = conversation_key
            if metadata.sdk_session_id:
                conversation.sdk_session_id = metadata.sdk_session_id
            if metadata.provider:
                conversation.provider = metadata.provider
            if metadata.provider_conversation_id:
                conversation.provider_conversation_id = metadata.provider_conversation_id
            if metadata.session_cursor:
                conversation.session_cursor = metadata.session_cursor
            if metadata.last_session_sync_at:
                conversation.last_session_sync_at = metadata.last_session_sync_at
            return conversation

            # not reached - early return above
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

    async def _get_conversation(
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

    async def _load_messages(
        self,
        session: AsyncSession,
        conversation_ids: list[uuid.UUID],
        *,
        tenant_id: uuid.UUID,
    ) -> dict[uuid.UUID, list[AgentMessage]]:
        if not conversation_ids:
            return {}
        segments = await _load_ledger_segments_bulk(
            session,
            tenant_id=tenant_id,
            conversation_ids=conversation_ids,
        )
        visibility_predicate = _message_visibility_predicate(segments)
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


def _ensure_metadata_tenant(metadata: ConversationMetadata, tenant_id: str) -> None:
    if metadata.tenant_id != tenant_id:
        raise ValueError("Metadata tenant_id mismatch")


async def _load_ledger_segments(
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


async def _load_ledger_segments_bulk(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_ids: list[uuid.UUID],
) -> list[ConversationLedgerSegment]:
    if not conversation_ids:
        return []
    result = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id.in_(conversation_ids),
        )
        .order_by(
            ConversationLedgerSegment.conversation_id.asc(),
            ConversationLedgerSegment.segment_index.asc(),
        )
    )
    return list(result.scalars().all())


def _message_visibility_predicate(segments: list[ConversationLedgerSegment]):
    """Build a SQL predicate that selects only the visible portion of each segment."""

    if not segments:
        return AgentMessage.id >= 0  # all messages (fallback; normally segments always exist)

    active_by_conversation: dict[uuid.UUID, int] = {}
    for seg in segments:
        if seg.truncated_at is None:
            active_by_conversation[seg.conversation_id] = (
                active_by_conversation.get(seg.conversation_id, 0) + 1
            )
    if any(count > 1 for count in active_by_conversation.values()):
        raise ValueError("Conversation ledger has multiple active segments")

    conditions = []
    for seg in segments:
        if seg.truncated_at is None:
            conditions.append(AgentMessage.segment_id == seg.id)
            continue

        max_pos = seg.visible_through_message_position
        if max_pos is None:
            raise ValueError("Truncated ledger segment missing visible_through_message_position")
        conditions.append(and_(AgentMessage.segment_id == seg.id, AgentMessage.position <= max_pos))

    return or_(*conditions) if conditions else AgentMessage.id < 0


__all__ = ["ConversationMessageStore"]
