from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from app.services.agent_service import AgentService, ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.conversation_service import ConversationService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Any, cast

from app.domain.conversations import ConversationNotFoundError
from app.infrastructure.persistence.conversations.postgres import (
    PostgresConversationRepository,
)


class _DummyResult:
    def __init__(self, rows: list[Any]):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):  # pragma: no cover - passthrough
        return self._rows


class _DummySession:
    def __init__(self, rows: list[Any] | None = None):
        self._rows = rows or []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def execute(self, stmt):  # pragma: no cover - stmt unused in stub
        return _DummyResult(self._rows)


def _repo_with_rows(rows: list[Any] | None = None) -> PostgresConversationRepository:
    session = _DummySession(rows)

    def session_factory() -> _DummySession:
        return session

    return PostgresConversationRepository(
        cast(async_sessionmaker[AsyncSession], session_factory)
    )


@pytest.mark.asyncio
async def test_get_run_events_raises_for_missing_conversation(monkeypatch: pytest.MonkeyPatch):
    repo = _repo_with_rows()
    monkeypatch.setattr(repo, "_get_conversation", AsyncMock(return_value=None))

    with pytest.raises(ConversationNotFoundError):
        await repo.get_run_events(str(uuid.uuid4()), tenant_id=str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_get_run_events_returns_empty_for_existing_conversation(monkeypatch: pytest.MonkeyPatch):
    repo = _repo_with_rows([])
    monkeypatch.setattr(repo, "_get_conversation", AsyncMock(return_value=object()))

    events = await repo.get_run_events(str(uuid.uuid4()), tenant_id=str(uuid.uuid4()))

    assert events == []


@pytest.mark.asyncio
async def test_event_projection_failure_does_not_bubble(monkeypatch: pytest.MonkeyPatch):
    # Minimal harness to exercise _ingest_new_session_items
    service = AgentService(conversation_service=ConversationService(repository=None))

    failing_projector = AsyncMock(spec=EventProjector)
    failing_projector.ingest_session_items.side_effect = RuntimeError("boom")
    monkeypatch.setattr(service, "_event_projector", failing_projector)

    class DummyHandle:
        def get_items(self):
            return [
                {"id": "pre"},
                {"id": "post"},
            ]

    # Should not raise even though projector blows up
    await service._ingest_new_session_items(
        session_handle=DummyHandle(),
        pre_items=[{"id": "pre"}],
        conversation_id="conv-1",
        tenant_id="tenant-1",
        agent="triage",
        model="gpt-5.1",
        response_id="resp-1",
    )

    failing_projector.ingest_session_items.assert_called_once()
