"""Contract tests for conversation endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload, override_current_user
from tests.utils.contract_env import TEST_TENANT_ID, configure_contract_env

configure_contract_env()

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.domain.ai import AgentRunResult  # noqa: E402
from app.domain.conversations import ConversationMessage, ConversationMetadata  # noqa: E402
from app.infrastructure.db.engine import init_engine  # noqa: E402
from app.services.agents import AgentService  # noqa: E402
from main import app  # noqa: E402
from tests.utils.agent_contract import default_agent_key  # noqa: E402


def _stub_current_user() -> dict[str, Any]:
    return make_user_payload()


@pytest_asyncio.fixture(autouse=True)
async def _ensure_engine_initialized() -> None:
    await init_engine(run_migrations=True)


@pytest.fixture(autouse=True)
def _override_current_user():
    with override_current_user(app, _stub_current_user):
        yield


@pytest.fixture(scope="function")
def client(_configure_agent_provider):
    with TestClient(app) as test_client:
        yield test_client


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_conversation_lifecycle(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Sure, let's get started.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    chat_request = {"message": "Start a new plan", "agent_type": default_agent_key()}
    chat_response = client.post("/api/v1/chat", json=chat_request)
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    history_response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["conversation_id"] == conversation_id
    assert len(history["messages"]) >= 2

    list_response = client.get("/api/v1/conversations")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert "items" in list_payload
    conversations = list_payload["items"]
    assert any(item["conversation_id"] == conversation_id for item in conversations)

    delete_response = client.delete(f"/api/v1/conversations/{conversation_id}")
    assert delete_response.status_code == 204


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_conversation_search_and_events(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Searchable content",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    chat_request = {"message": "Searchable content", "agent_type": default_agent_key()}
    chat_response = client.post("/api/v1/chat", json=chat_request)
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    search_response = client.get("/api/v1/conversations/search", params={"q": "Searchable"})
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert "items" in search_payload
    assert isinstance(search_payload["items"], list)

    events_response = client.get(f"/api/v1/conversations/{conversation_id}/events")
    assert events_response.status_code == 200
    events_payload = events_response.json()
    assert "items" in events_payload
    assert isinstance(events_payload["items"], list)


def test_delete_requires_delete_scope(client: TestClient) -> None:
    def _no_delete_user() -> dict[str, Any]:
        return make_user_payload(scope="conversations:read conversations:write")

    with override_current_user(app, _no_delete_user):
        response = client.delete("/api/v1/conversations/test-id")
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_conversation_repository_roundtrip(agent_service: AgentService) -> None:
    repository = agent_service.conversation_repository
    await repository.clear_conversation("integration-test", tenant_id=TEST_TENANT_ID)

    await repository.add_message(
        "integration-test",
        ConversationMessage(role="user", content="Test message"),
        tenant_id=TEST_TENANT_ID,
        metadata=ConversationMetadata(
            tenant_id=TEST_TENANT_ID,
            agent_entrypoint=default_agent_key(),
        ),
    )

    messages = await repository.get_messages("integration-test", tenant_id=TEST_TENANT_ID)
    assert len(messages) == 1
    assert messages[0].content == "Test message"

    await repository.clear_conversation("integration-test", tenant_id=TEST_TENANT_ID)
    assert await repository.get_messages("integration-test", tenant_id=TEST_TENANT_ID) == []
