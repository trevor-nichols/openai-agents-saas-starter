"""Persistence helpers for per-run usage audit records."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import ConversationRunUsage
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.mappers import to_utc
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentRunUsageModel,
)


class RunUsageStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        usage: ConversationRunUsage,
    ) -> None:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            await self._insert_usage(session, conversation_uuid, tenant_uuid, usage)
            await session.commit()

    async def list_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int = 20,
    ) -> list[ConversationRunUsage]:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentRunUsageModel)
                .join(AgentConversation, AgentConversation.id == AgentRunUsageModel.conversation_id)
                .where(
                    AgentRunUsageModel.conversation_id == conversation_uuid,
                    AgentRunUsageModel.tenant_id == tenant_uuid,
                )
                .order_by(AgentRunUsageModel.created_at.desc())
                .limit(limit)
            )
            rows: Iterable[AgentRunUsageModel] = result.scalars().all()
            return [self._to_domain(row) for row in rows]

    async def _insert_usage(
        self,
        session: AsyncSession,
        conversation_uuid,
        tenant_uuid,
        usage: ConversationRunUsage,
    ) -> None:
        model = AgentRunUsageModel(
            tenant_id=tenant_uuid,
            conversation_id=conversation_uuid,
            response_id=usage.response_id,
            run_id=usage.run_id,
            agent_key=usage.agent_key,
            provider=usage.provider,
            requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            reasoning_output_tokens=usage.reasoning_output_tokens,
            request_usage_entries=usage.request_usage_entries,
            created_at=to_utc(usage.created_at) if usage.created_at else datetime.utcnow(),
        )
        session.add(model)

        # Increment aggregates on conversation for quick reads.
        await session.execute(
            update(AgentConversation)
            .where(AgentConversation.id == conversation_uuid)
            .values(
                total_tokens_prompt=
                AgentConversation.total_tokens_prompt + (usage.input_tokens or 0),
                total_tokens_completion=
                AgentConversation.total_tokens_completion + (usage.output_tokens or 0),
                reasoning_tokens=
                AgentConversation.reasoning_tokens + (usage.reasoning_output_tokens or 0),
                total_cached_input_tokens=
                AgentConversation.total_cached_input_tokens + (usage.cached_input_tokens or 0),
                total_requests=AgentConversation.total_requests + (usage.requests or 1),
                updated_at=datetime.utcnow(),
            )
        )

    def _to_domain(self, row: AgentRunUsageModel) -> ConversationRunUsage:
        return ConversationRunUsage(
            conversation_id=str(row.conversation_id),
            response_id=row.response_id,
            run_id=row.run_id,
            agent_key=row.agent_key,
            provider=row.provider,
            requests=row.requests,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            total_tokens=row.total_tokens,
            cached_input_tokens=row.cached_input_tokens,
            reasoning_output_tokens=row.reasoning_output_tokens,
            request_usage_entries=list(row.request_usage_entries)
            if row.request_usage_entries is not None
            else None,
            created_at=row.created_at,
        )


__all__ = ["RunUsageStore"]
