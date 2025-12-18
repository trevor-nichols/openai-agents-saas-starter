from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies.tenant import TenantContext, TenantRole
from app.api.v1.openai_files.router import download_openai_container_file
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.ledger_query_store import ConversationLedgerQueryStore
from app.infrastructure.persistence.conversations.models import AgentConversation, TenantAccount
from app.infrastructure.persistence.models.base import Base
from app.services.containers.service import ContainerService
from app.services.containers.service import ContainerNotFoundError


class _DummyContainerFilesClient:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def content(self, *, container_id: str, file_id: str):  # pragma: no cover - shape only
        return _DummyContentResponse(self._payload)


class _DummyContentResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def aread(self) -> bytes:
        return self._payload


class _DummyOpenAIClient:
    def __init__(self, payload: bytes) -> None:
        self.containers = type(
            "_Containers",
            (),
            {"files": _DummyContainerFilesClient(payload)},
        )()


class _AlwaysMissingContainerService:
    async def get_container_by_openai_id(self, *, openai_container_id: str, tenant_id: UUID):
        raise ContainerNotFoundError("not found")


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


async def _seed_ledger_container_file_citation(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    conversation_id: UUID,
    container_id: str,
    file_id: str,
) -> None:
    payload = {
        "schema": "public_sse_v1",
        "event_id": 1,
        "stream_id": "stream_test",
        "server_timestamp": "2025-12-15T12:00:00Z",
        "kind": "message.citation",
        "conversation_id": str(conversation_id),
        "response_id": "resp_test",
        "agent": "code_assistant",
        "item_id": "msg_001",
        "output_index": 1,
        "content_index": 0,
        "citation": {
            "type": "container_file_citation",
            "start_index": 0,
            "end_index": 10,
            "container_id": container_id,
            "file_id": file_id,
            "filename": "report.pdf",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    async with session_factory() as session:
        session.add(TenantAccount(id=tenant_id, slug="test-tenant", name="Test Tenant"))
        session.add(
            AgentConversation(
                id=conversation_id,
                conversation_key=str(conversation_id),
                tenant_id=tenant_id,
                user_id=None,
                agent_entrypoint="code_assistant",
                active_agent="code_assistant",
                provider="openai",
                provider_conversation_id=None,
            )
        )

        segment_id = uuid4()
        session.add(
            ConversationLedgerSegment(
                id=segment_id,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                segment_index=0,
                parent_segment_id=None,
                visible_through_event_id=None,
                visible_through_message_position=None,
                truncated_at=None,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
        )

        session.add(
            ConversationLedgerEvent(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                segment_id=segment_id,
                schema_version="public_sse_v1",
                kind="message.citation",
                stream_id="stream_test",
                event_id=1,
                server_timestamp=datetime.now(tz=UTC),
                response_id="resp_test",
                agent="code_assistant",
                workflow_run_id=None,
                provider_sequence_number=None,
                output_index=1,
                item_id="msg_001",
                content_index=0,
                tool_call_id=None,
                payload_size_bytes=len(payload_bytes),
                payload_json=payload,
                payload_object_id=None,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_download_container_file_allows_ledger_citation_when_container_missing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid4()
    conversation_id = uuid4()
    container_id = "cntr_test"
    file_id = "cfile_test"

    await _seed_ledger_container_file_citation(
        session_factory,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        container_id=container_id,
        file_id=file_id,
    )

    response = await download_openai_container_file(
        container_id=container_id,
        file_id=file_id,
        conversation_id=str(conversation_id),
        filename="report.pdf",
        tenant_context=TenantContext(
            tenant_id=str(tenant_id),
            role=TenantRole.VIEWER,
            user={"user_id": "u"},
        ),
        client=cast(AsyncOpenAI, _DummyOpenAIClient(b"hello")),
        containers=cast(ContainerService, _AlwaysMissingContainerService()),
        ledger=ConversationLedgerQueryStore(session_factory),
    )

    assert response.status_code == 200
    assert response.body == b"hello"
    assert response.headers["Content-Disposition"] == 'attachment; filename="report.pdf"'


@pytest.mark.asyncio
async def test_download_container_file_denies_without_conversation_id_when_container_missing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid4()
    conversation_id = uuid4()
    container_id = "cntr_test"
    file_id = "cfile_test"

    await _seed_ledger_container_file_citation(
        session_factory,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        container_id=container_id,
        file_id=file_id,
    )

    with pytest.raises(HTTPException) as exc:
        await download_openai_container_file(
            container_id=container_id,
            file_id=file_id,
            conversation_id=None,
            filename="report.pdf",
            tenant_context=TenantContext(
                tenant_id=str(tenant_id),
                role=TenantRole.VIEWER,
                user={"user_id": "u"},
            ),
            client=cast(AsyncOpenAI, _DummyOpenAIClient(b"hello")),
            containers=cast(ContainerService, _AlwaysMissingContainerService()),
            ledger=ConversationLedgerQueryStore(session_factory),
        )

    assert exc.value.status_code == 404
