from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.domain.conversations import ConversationSummary as DomainSummary
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    ConversationSummary,
    TenantAccount,
)
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.persistence.conversations.summary_store import ConversationSummaryStore


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_latest_summary_returns_domain_object(session_factory: async_sessionmaker[AsyncSession]) -> None:
    tenant_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    async with session_factory() as session:
        tenant = TenantAccount(id=tenant_id, slug="acme", name="Acme Corp")
        convo = AgentConversation(
            id=conversation_id,
            conversation_key="conv-key",
            tenant_id=tenant_id,
            agent_entrypoint="default",
        )
        session.add_all([tenant, convo])
        await session.commit()

    async with session_factory() as session:
        session.add(
            ConversationSummary(
                id=1,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                agent_key="agent-1",
                summary_text="hello summary",
                summary_model="gpt-5.1",
                summary_length_tokens=42,
                version="v1",
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

    store = ConversationSummaryStore(session_factory)
    result = await store.get_latest_summary(
        conversation_id=str(conversation_id),
        tenant_id=str(tenant_id),
        agent_key="agent-1",
    )

    assert isinstance(result, DomainSummary)
    assert result.summary_text == "hello summary"
    assert result.summary_model == "gpt-5.1"
    assert result.summary_length_tokens == 42
    assert result.version == "v1"
