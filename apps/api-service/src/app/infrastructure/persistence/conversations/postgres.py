"""Postgres-backed conversation repository implementation."""

from __future__ import annotations

import base64
import json
import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from time import perf_counter
from typing import Literal, cast

from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import (
    ConversationAttachment,
    ConversationEvent,
    ConversationMessage,
    ConversationMetadata,
    ConversationNotFoundError,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationSearchHit,
    ConversationSearchPage,
    ConversationSessionState,
)
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
    AgentRunEvent,
)
from app.observability.metrics import (
    AGENT_RUN_EVENTS_DRIFT,
    AGENT_RUN_EVENTS_PROJECTION_DURATION_SECONDS,
    AGENT_RUN_EVENTS_PROJECTION_TOTAL,
    AGENT_RUN_EVENTS_READ_DURATION_SECONDS,
    AGENT_RUN_EVENTS_READ_TOTAL,
    _sanitize_agent,
    _sanitize_tenant,
)

logger = logging.getLogger("api-service.persistence")

_CONVERSATION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "api-service:conversation")
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


def _parse_tenant_id(value: str | None) -> uuid.UUID:
    if not value:
        raise ValueError("tenant_id is required")
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - invalid user input
        raise ValueError("tenant_id must be a valid UUID") from exc


def _encode_cursor(ts: datetime, conversation_id: uuid.UUID) -> str:
    payload = {"ts": ts.isoformat(), "id": str(conversation_id)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        ts = datetime.fromisoformat(data["ts"])
        conv_id = uuid.UUID(data["id"])
        return ts, conv_id
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid pagination cursor") from exc


def _encode_search_cursor(rank: float, ts: datetime, conversation_id: uuid.UUID) -> str:
    payload = {"rank": rank, "ts": ts.isoformat(), "id": str(conversation_id)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_search_cursor(cursor: str) -> tuple[float, datetime, uuid.UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        rank = float(data["rank"])
        ts = datetime.fromisoformat(data["ts"])
        conv_id = uuid.UUID(data["id"])
        return rank, ts, conv_id
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid search pagination cursor") from exc


class PostgresConversationRepository(ConversationRepository):
    """Persist conversations and messages using PostgreSQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        conversation_key = _derive_conversation_key(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
        _ensure_metadata_tenant(metadata, tenant_id)
        async with self._session_factory() as session:
            conversation = await self._get_or_create_conversation(
                session,
                conversation_uuid,
                conversation_key=conversation_key,
                tenant_id=tenant_uuid,
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
                position=position,
                role=message.role,
                agent_type=metadata.active_agent if message.role == "assistant" else None,
                content={"text": message.content},
                attachments=_serialize_attachments(message.attachments),
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

    async def get_messages(
        self, conversation_id: str, *, tenant_id: str
    ) -> list[ConversationMessage]:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            try:
                conversation = await self._get_conversation(
                    session,
                    conversation_uuid,
                    tenant_id=tenant_uuid,
                    strict=True,
                )
            except ValueError as exc:
                raise ConversationNotFoundError(str(exc)) from exc
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

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
                    attachments=_extract_attachments(row.attachments),
                    timestamp=row.created_at,
                )
                for row in rows
            ]

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        tenant_uuid = _parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentConversation.conversation_key).where(
                    AgentConversation.tenant_id == tenant_uuid
                )
            )
            return [row[0] for row in result.all()]

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]:
        tenant_uuid = _parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversations = await session.execute(
                select(AgentConversation)
                .where(AgentConversation.tenant_id == tenant_uuid)
                .order_by(AgentConversation.updated_at.desc())
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
                        attachments=_extract_attachments(item.attachments),
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

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage:
        tenant_uuid = _parse_tenant_id(tenant_id)
        limit = max(1, min(limit, 100))

        cursor_ts: datetime | None = None
        cursor_uuid: uuid.UUID | None = None
        if cursor:
            cursor_ts, cursor_uuid = _decode_cursor(cursor)

        filters = [AgentConversation.tenant_id == tenant_uuid]
        if agent_entrypoint:
            filters.append(AgentConversation.agent_entrypoint == agent_entrypoint)
        if updated_after:
            filters.append(AgentConversation.updated_at >= _to_utc(updated_after))
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
                next_cursor = _encode_cursor(tail.updated_at, tail.id)
                rows = rows[:limit]

            if not rows:
                return ConversationPage(items=[], next_cursor=None)

            ids = [conversation.id for conversation in rows]
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
            for conversation in rows:
                entries = grouped.get(conversation.id, [])
                messages_list = [
                    ConversationMessage(
                        role=_coerce_role(item.role),
                        content=_extract_message_content(item.content),
                        attachments=_extract_attachments(item.attachments),
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

            return ConversationPage(items=records, next_cursor=next_cursor)

    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage:
        tenant_uuid = _parse_tenant_id(tenant_id)
        limit = max(1, min(limit, 50))
        if not query.strip():
            raise ValueError("Query cannot be empty")

        cursor_rank: float | None = None
        cursor_ts: datetime | None = None
        cursor_uuid: uuid.UUID | None = None
        if cursor:
            cursor_rank, cursor_ts, cursor_uuid = _decode_search_cursor(cursor)

        async with self._session_factory() as session:
            dialect = session.bind.dialect.name if session.bind else ""
            base_filters = [AgentConversation.tenant_id == tenant_uuid]
            if agent_entrypoint:
                base_filters.append(AgentConversation.agent_entrypoint == agent_entrypoint)

            # Build search query.
            if dialect == "postgresql":
                ts_query = func.plainto_tsquery("english", query)
                rank_expr = func.ts_rank_cd(AgentMessage.text_tsv, ts_query)
                search_filter = AgentMessage.text_tsv.op("@@")(ts_query)
            else:
                rank_expr = func.length(AgentMessage.content.cast(String))
                search_filter = func.lower(AgentMessage.content.cast(String)).like(
                    f"%{query.lower()}%"
                )

            base_query = (
                select(
                    AgentConversation.id.label("cid"),
                    AgentConversation.updated_at.label("updated_at"),
                    func.max(rank_expr).label("rank"),
                )
                .join(AgentMessage, AgentMessage.conversation_id == AgentConversation.id)
                .where(*base_filters, search_filter)
                .group_by(AgentConversation.id, AgentConversation.updated_at)
            )

            if cursor_rank is not None and cursor_ts and cursor_uuid:
                base_query = base_query.having(
                    or_(
                        func.max(rank_expr) < cursor_rank,
                        and_(
                            func.max(rank_expr) == cursor_rank,
                            or_(
                                AgentConversation.updated_at < cursor_ts,
                                and_(
                                    AgentConversation.updated_at == cursor_ts,
                                    AgentConversation.id < cursor_uuid,
                                ),
                            ),
                        ),
                    )
                )

            ranked = base_query.subquery()

            result = await session.execute(
                select(AgentConversation, ranked.c.rank)
                .join(ranked, AgentConversation.id == ranked.c.cid)
                .order_by(
                    ranked.c.rank.desc(),
                    AgentConversation.updated_at.desc(),
                    AgentConversation.id.desc(),
                )
                .limit(limit + 1)
            )

            rows = result.all()
            next_cursor = None
            if len(rows) > limit:
                tail_conv, tail_rank = rows[limit]
                next_cursor = _encode_search_cursor(
                    float(tail_rank or 0.0), tail_conv.updated_at, tail_conv.id
                )
                rows = rows[:limit]

            if not rows:
                return ConversationSearchPage(items=[], next_cursor=None)

            ids = [row[0].id for row in rows]
            messages = await session.execute(
                select(AgentMessage)
                .where(AgentMessage.conversation_id.in_(ids))
                .order_by(AgentMessage.conversation_id, AgentMessage.position)
            )
            message_rows: Sequence[AgentMessage] = messages.scalars().all()
            grouped: dict[uuid.UUID, list[AgentMessage]] = {}
            for row in message_rows:
                grouped.setdefault(row.conversation_id, []).append(row)

            hits: list[ConversationSearchHit] = []
            for conversation, rank in rows:
                entries = grouped.get(conversation.id, [])
                messages_list = [
                    ConversationMessage(
                        role=_coerce_role(item.role),
                        content=_extract_message_content(item.content),
                        attachments=_extract_attachments(item.attachments),
                        timestamp=item.created_at,
                    )
                    for item in entries
                ]
                hits.append(
                    ConversationSearchHit(
                        record=ConversationRecord(
                            conversation_id=conversation.conversation_key,
                            messages=messages_list,
                        ),
                        score=float(rank or 0.0),
                    )
                )

            return ConversationSearchPage(items=hits, next_cursor=next_cursor)

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
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
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
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

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
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

    async def add_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationEvent],
    ) -> None:
        if not events:
            return
        op_start = perf_counter()
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)

        async with self._session_factory() as session:
            conversation = await self._get_conversation(
                session,
                conversation_uuid,
                tenant_id=tenant_uuid,
                strict=True,
            )
            if conversation is None:
                raise ValueError(f"Conversation {conversation_id} does not exist")

            # Determine the next sequence number to preserve ordering.
            current_seq = await session.execute(
                select(func.coalesce(func.max(AgentRunEvent.sequence_no), -1)).where(
                    AgentRunEvent.conversation_id == conversation_uuid
                )
            )
            start_seq = int(current_seq.scalar_one() or -1) + 1

            # Deduplicate on response_id when present to keep idempotence.
            response_ids = {ev.response_id for ev in events if ev.response_id}
            existing_keys: set[tuple[str | None, str | None, str | None]] = set()
            if response_ids:
                result = await session.execute(
                    select(
                        AgentRunEvent.response_id,
                        AgentRunEvent.run_item_name,
                        AgentRunEvent.tool_call_id,
                    )
                    .where(
                        AgentRunEvent.conversation_id == conversation_uuid,
                        AgentRunEvent.response_id.in_(response_ids),
                    )
                )
                existing_keys = {(row[0], row[1], row[2]) for row in result.all()}

            rows: list[AgentRunEvent] = []
            seq = start_seq
            for event in events:
                key = (event.response_id, event.run_item_name, event.tool_call_id)
                if event.response_id and key in existing_keys:
                    continue

                rows.append(
                    AgentRunEvent(
                        conversation_id=conversation_uuid,
                        sequence_no=event.sequence_no if event.sequence_no is not None else seq,
                        response_id=event.response_id,
                        workflow_run_id=event.workflow_run_id,
                        run_item_type=event.run_item_type,
                        run_item_name=event.run_item_name,
                        role=event.role,
                        agent=event.agent,
                        tool_call_id=event.tool_call_id,
                        tool_name=event.tool_name,
                        model=event.model,
                        content_text=event.content_text,
                        reasoning_text=event.reasoning_text,
                        call_arguments=_coerce_mapping(event.call_arguments),
                        call_output=_coerce_mapping(event.call_output),
                        attachments=_serialize_attachments(event.attachments),
                        created_at=_to_utc(event.timestamp),
                        ingested_at=datetime.now(UTC),
                    )
                )
                seq += 1

            if rows:
                session.add_all(rows)
                agent_label = _sanitize_agent(events[0].agent if events else None)
                tenant_label = _sanitize_tenant(tenant_id)
                try:
                    await session.commit()
                except IntegrityError:
                    AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
                        tenant=tenant_label,
                        agent=agent_label,
                        result="conflict",
                    ).inc()
                    await session.rollback()
                    raise
                except Exception:
                    AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
                        tenant=tenant_label,
                        agent=agent_label,
                        result="error",
                    ).inc()
                    await session.rollback()
                    raise
                else:
                    AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
                        tenant=tenant_label,
                        agent=agent_label,
                        result="success",
                    ).inc()
                    AGENT_RUN_EVENTS_PROJECTION_DURATION_SECONDS.labels(
                        tenant=tenant_label,
                        agent=agent_label,
                    ).observe(perf_counter() - op_start)

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        include_types: set[str] | None = None,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        op_start = perf_counter()
        conversation_uuid = _coerce_conversation_uuid(conversation_id)
        tenant_uuid = _parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            try:
                conversation = await self._get_conversation(
                    session,
                    conversation_uuid,
                    tenant_id=tenant_uuid,
                    strict=True,
                )
            except ValueError as exc:
                raise ConversationNotFoundError(str(exc)) from exc

            if conversation is None:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            stmt = select(AgentRunEvent).where(AgentRunEvent.conversation_id == conversation_uuid)
            if include_types:
                stmt = stmt.where(AgentRunEvent.run_item_type.in_(include_types))
            if workflow_run_id:
                stmt = stmt.where(AgentRunEvent.workflow_run_id == workflow_run_id)
            stmt = stmt.order_by(AgentRunEvent.sequence_no)

            result = await session.execute(stmt)
            rows: Sequence[AgentRunEvent] = result.scalars().all()
            events = [
                ConversationEvent(
                    run_item_type=row.run_item_type,
                    run_item_name=row.run_item_name,
                    role=_coerce_role(row.role) if row.role else None,
                    agent=row.agent,
                    tool_call_id=row.tool_call_id,
                    tool_name=row.tool_name,
                    model=row.model,
                    content_text=row.content_text,
                    reasoning_text=row.reasoning_text,
                    call_arguments=row.call_arguments or None,
                    call_output=row.call_output or None,
                    attachments=_extract_attachments(row.attachments),
                    response_id=row.response_id,
                    sequence_no=row.sequence_no,
                    workflow_run_id=row.workflow_run_id,
                    timestamp=row.created_at,
                )
                for row in rows
            ]
            # Update drift gauge if sdk message count is available via related table.
            try:
                sdk_count = conversation.message_count
                drift = sdk_count - len(events)
                AGENT_RUN_EVENTS_DRIFT.labels(
                    tenant=_sanitize_tenant(tenant_id),
                    conversation_id=str(conversation_uuid),
                ).set(drift)
            except Exception:  # pragma: no cover - best-effort metric
                logger.debug("drift_gauge_update_failed", exc_info=True)

            tenant_label = _sanitize_tenant(tenant_id)
            mode_label = "filtered" if include_types else "full"
            AGENT_RUN_EVENTS_READ_TOTAL.labels(
                tenant=tenant_label,
                mode=mode_label,
                result="success",
            ).inc()
            AGENT_RUN_EVENTS_READ_DURATION_SECONDS.labels(
                tenant=tenant_label,
                mode=mode_label,
            ).observe(perf_counter() - op_start)
            return events

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
                raise ValueError(
                    "Conversation belongs to a different tenant; refusing to continue."
                )
            return None
        return conversation


def _ensure_metadata_tenant(metadata: ConversationMetadata, tenant_id: str) -> None:
    if metadata.tenant_id != tenant_id:
        raise ValueError("Metadata tenant_id mismatch")


def _extract_message_content(payload: dict[str, object] | str | None) -> str:
    if isinstance(payload, dict):
        if "text" in payload:
            return str(payload["text"])
        return str(payload)
    if isinstance(payload, str):
        return payload
    return ""


def _extract_attachments(payload: list[dict[str, object]] | None) -> list[ConversationAttachment]:
    if not payload:
        return []
    attachments: list[ConversationAttachment] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        mime = item.get("mime_type")
        mime_str = str(mime) if isinstance(mime, str) else None
        size_val = item.get("size_bytes")
        size_int = int(size_val) if isinstance(size_val, int) else None
        tool_call = item.get("tool_call_id")
        tool_call_str = str(tool_call) if isinstance(tool_call, str) else None
        attachments.append(
            ConversationAttachment(
                object_id=str(item.get("object_id", "")),
                filename=str(item.get("filename", "")),
                mime_type=mime_str,
                size_bytes=size_int,
                presigned_url=None,
                tool_call_id=tool_call_str,
            )
        )
    return attachments


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _coerce_mapping(value: object | None) -> dict[str, object] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"value": value}
def _coerce_role(value: str) -> MessageRole:
    if value not in _MESSAGE_ROLES:
        raise ValueError(f"Unsupported conversation role '{value}'")
    return cast(MessageRole, value)


def _serialize_attachments(attachments: list[ConversationAttachment]) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for item in attachments:
        serialized.append(
            {
                "object_id": item.object_id,
                "filename": item.filename,
                "mime_type": item.mime_type,
                "size_bytes": item.size_bytes,
                "tool_call_id": item.tool_call_id,
            }
        )
    return serialized
