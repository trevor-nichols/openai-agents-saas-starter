"""Conversation ledger persistence (public_sse_v1 frames)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversation_ledger import ConversationLedgerEventRecord
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.ledger_segments import (
    get_or_create_active_segment,
)
from app.infrastructure.persistence.conversations.models import AgentConversation


class ConversationLedgerStore:
    """Store for durable public stream frames used for exact UI replay."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: Sequence[ConversationLedgerEventRecord],
    ) -> None:
        if not events:
            return

        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)

        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
                raise ValueError(f"Conversation {conversation_id} does not exist")

            segment = await self._get_or_create_active_segment(
                session, tenant_id=tenant_uuid, conversation_id=conversation_uuid
            )

            rows: list[ConversationLedgerEvent] = []
            for record in events:
                rows.append(
                    ConversationLedgerEvent(
                        tenant_id=tenant_uuid,
                        conversation_id=conversation_uuid,
                        segment_id=segment.id,
                        schema_version=record.schema_version,
                        kind=record.kind,
                        stream_id=record.stream_id,
                        event_id=record.event_id,
                        server_timestamp=record.server_timestamp,
                        response_id=record.response_id,
                        agent=record.agent,
                        workflow_run_id=record.workflow_run_id,
                        provider_sequence_number=record.provider_sequence_number,
                        output_index=record.output_index,
                        item_id=record.item_id,
                        content_index=record.content_index,
                        tool_call_id=record.tool_call_id,
                        payload_size_bytes=record.payload_size_bytes,
                        payload_json=record.payload_json,
                        payload_object_id=record.payload_object_id,
                    )
                )

            session.add_all(rows)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    async def _get_or_create_active_segment(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> ConversationLedgerSegment:
        return await get_or_create_active_segment(
            session,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )


__all__ = ["ConversationLedgerStore"]
