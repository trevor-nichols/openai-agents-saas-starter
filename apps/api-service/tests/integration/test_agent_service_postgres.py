"""Postgres-backed smoke test for AgentService wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.v1.chat.schemas import AgentChatRequest
from app.bootstrap import reset_container
from app.core import settings as config_module
from app.domain.ai import AgentRunResult
from app.infrastructure.persistence.conversations.postgres import (
    PostgresConversationRepository,
)
from app.infrastructure.providers.openai import build_openai_provider
from app.services.agent_service import ConversationActorContext, get_agent_service
from app.services.agents.provider_registry import get_provider_registry
from app.services.conversation_service import conversation_service

pytestmark = pytest.mark.postgres


@pytest.fixture
def _pg_session_factory(
    migrated_engine: AsyncEngine,
) -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    session_factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    return session_factory, migrated_engine


@pytest.mark.asyncio
async def test_agent_service_persists_messages_postgres(
    _pg_session_factory: tuple[async_sessionmaker[AsyncSession], AsyncEngine],
) -> None:
    session_factory, engine = _pg_session_factory
    repository = PostgresConversationRepository(session_factory)

    container = reset_container()
    container.conversation_service.set_repository(repository)

    registry = get_provider_registry()
    registry.clear()
    registry.register(
        build_openai_provider(
            settings_factory=config_module.get_settings,
            conversation_searcher=conversation_service.search,
            engine=engine,
            auto_create_tables=False,
        ),
        set_default=True,
    )
    container.agent_service = None
    service = get_agent_service()

    actor = ConversationActorContext(tenant_id="tenant-pg", user_id="user-pg")
    request = AgentChatRequest(message="Hello durable world", agent_type="triage")

    with patch(
        "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = AgentRunResult(
            final_output="Hi back",
            response_id="resp",
            usage=None,
        )

        response = await service.chat(request, actor=actor)

    messages = await repository.get_messages(response.conversation_id, tenant_id=actor.tenant_id)
    contents = [msg.content for msg in messages]
    assert contents[:2] == ["Hello durable world", "Hi back"]
    assert response.agent_used == "triage"
