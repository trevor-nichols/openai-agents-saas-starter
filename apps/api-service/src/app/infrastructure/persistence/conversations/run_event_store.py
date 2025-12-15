"""Run-event persistence and projection helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from time import perf_counter

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import ConversationEvent, ConversationNotFoundError
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.instrumentation import RunEventMetrics
from app.infrastructure.persistence.conversations.mappers import (
    coerce_mapping,
    run_event_from_row,
    serialize_attachments,
    to_utc,
)
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentRunEvent


class RunEventStore:
    """Isolated run-event projection logic."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)

        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
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
            batch_keys: set[tuple[str | None, str | None, str | None]] = set()
            seq = start_seq
            for event in events:
                key = (event.response_id, event.run_item_name, event.tool_call_id)
                if event.response_id:
                    if key in existing_keys:
                        continue
                    if key in batch_keys:
                        continue
                    batch_keys.add(key)

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
                        call_arguments=coerce_mapping(event.call_arguments),
                        call_output=coerce_mapping(event.call_output),
                        attachments=serialize_attachments(event.attachments),
                        created_at=to_utc(event.timestamp),
                        ingested_at=datetime.now(UTC),
                    )
                )
                seq += 1

            if not rows:
                return

            metrics = RunEventMetrics(tenant_id, events[0].agent if events else None)
            session.add_all(rows)
            try:
                await session.commit()
            except IntegrityError:
                metrics.projection_conflict()
                await session.rollback()
                raise
            except Exception:
                metrics.projection_error()
                await session.rollback()
                raise
            else:
                metrics.projection_success(op_start)

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        op_start = perf_counter()
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            stmt = select(AgentRunEvent).where(AgentRunEvent.conversation_id == conversation_uuid)
            if workflow_run_id:
                stmt = stmt.where(AgentRunEvent.workflow_run_id == workflow_run_id)
            stmt = stmt.order_by(AgentRunEvent.sequence_no)

            result = await session.execute(stmt)
            rows: Sequence[AgentRunEvent] = result.scalars().all()
            events = [run_event_from_row(row) for row in rows]

            try:
                sdk_count = conversation.message_count
                drift = sdk_count - len(events)
                RunEventMetrics.set_drift_gauge(tenant_id, str(conversation_uuid), drift)
            except Exception:  # pragma: no cover - best-effort metric
                pass

            RunEventMetrics(tenant_id).read_success(op_start)
            return events


__all__ = ["RunEventStore"]
