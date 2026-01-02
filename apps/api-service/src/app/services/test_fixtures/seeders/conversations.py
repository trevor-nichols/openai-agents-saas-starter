"""Conversation seeding helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.conversations.ids import coerce_conversation_uuid
from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.test_fixtures.schemas import (
    FixtureConversation,
    FixtureConversationResult,
    FixtureUserResult,
)
from app.services.test_fixtures.seeders.resolve import resolve_user_id


async def ensure_conversations(
    session: AsyncSession,
    tenant: TenantAccount,
    user_results: dict[str, FixtureUserResult],
    conversations: list[FixtureConversation],
) -> dict[str, FixtureConversationResult]:
    results: dict[str, FixtureConversationResult] = {}
    now = datetime.now(UTC)
    for convo in conversations:
        expected_id = coerce_conversation_uuid(convo.key)
        existing = await session.scalar(
            select(AgentConversation).where(
                AgentConversation.tenant_id == tenant.id,
                AgentConversation.conversation_key == convo.key,
            )
        )
        if existing is not None and existing.id != expected_id:
            await session.delete(existing)
            await session.flush()
            existing = None
        if existing is None:
            conversation = AgentConversation(
                id=expected_id,
                conversation_key=convo.key,
                tenant_id=tenant.id,
                user_id=resolve_user_id(convo.user_email, user_results),
                agent_entrypoint=convo.agent_entrypoint,
                status=convo.status,
                created_at=now,
                updated_at=now,
                last_message_at=now if convo.messages else None,
            )
            session.add(conversation)
        else:
            conversation = existing
            conversation.agent_entrypoint = convo.agent_entrypoint
            conversation.status = convo.status
            conversation.user_id = resolve_user_id(convo.user_email, user_results)
            conversation.updated_at = now
            conversation.last_message_at = now if convo.messages else conversation.last_message_at

        await session.execute(
            delete(AgentMessage).where(AgentMessage.conversation_id == conversation.id)
        )
        await session.execute(
            delete(ConversationLedgerSegment).where(
                ConversationLedgerSegment.conversation_id == conversation.id
            )
        )

        # Ensure conversation row exists before inserting ledger segments.
        # Autoflush is disabled.
        await session.flush()

        segment_id = uuid4()
        session.add(
            ConversationLedgerSegment(
                id=segment_id,
                tenant_id=tenant.id,
                conversation_id=conversation.id,
                segment_index=0,
                created_at=now,
                updated_at=now,
            )
        )

        for index, message in enumerate(convo.messages):
            random_bits = cast(int, uuid4().int)
            message_id = random_bits & ((1 << 63) - 1)
            session.add(
                AgentMessage(
                    id=message_id,
                    conversation_id=conversation.id,
                    segment_id=segment_id,
                    position=index,
                    role=message.role,
                    content={"type": "text", "text": message.text},
                )
            )

        conversation.message_count = len(convo.messages)
        conversation.total_tokens_prompt = 0
        conversation.total_tokens_completion = 0

        results[convo.key] = FixtureConversationResult(
            conversation_id=str(conversation.id),
            status=conversation.status,
        )
    return results


__all__ = ["ensure_conversations"]
