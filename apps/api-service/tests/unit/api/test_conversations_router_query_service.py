from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.conversations import router


def _dummy_request(method: str = "GET") -> SimpleNamespace:
    return SimpleNamespace(method=method, url=SimpleNamespace(path="/"))


class StubQueryService:
    def __init__(self):
        self.called_with = None
        self.messages_called_with = None

    async def list_summaries(self, **kwargs):
        self.called_with = kwargs
        return (
            [
                {
                    "conversation_id": "c1",
                    "agent_entrypoint": "triage",
                    "active_agent": "triage",
                    "topic_hint": "Hi",
                    "status": "active",
                    "message_count": 2,
                    "last_message_preview": "hello",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:01Z",
                }
            ],
            "cursor-1",
        )

    async def get_messages_page(self, conversation_id, **kwargs):
        self.messages_called_with = (conversation_id, kwargs)
        return (
            [
                {
                    "role": "assistant",
                    "content": "hello",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "attachments": [],
                }
            ],
            "next-msg-cursor",
        )


@pytest.mark.asyncio
async def test_list_conversations_uses_query_service(monkeypatch):
    stub = StubQueryService()

    monkeypatch.setattr(router, "get_conversation_query_service", lambda: stub)
    monkeypatch.setattr(
        router,
        "resolve_tenant_context",
        AsyncMock(
            return_value=SimpleNamespace(
                tenant_id="t1", tenant_role="admin", ensure_role=lambda *args: None
            )
        ),
    )

    response = await router.list_conversations(
        request=_dummy_request(),
        current_user={"user_id": "u1"},
        tenant_id_header=None,
        tenant_role_header=None,
        limit=10,
        cursor=None,
        agent=None,
    )

    assert stub.called_with is not None
    assert stub.called_with["actor"].tenant_id == "t1"
    assert response.items[0].conversation_id == "c1"
    assert response.next_cursor == "cursor-1"


@pytest.mark.asyncio
async def test_get_conversation_messages_uses_query_service(monkeypatch):
    stub = StubQueryService()

    monkeypatch.setattr(router, "get_conversation_query_service", lambda: stub)
    monkeypatch.setattr(
        router,
        "resolve_tenant_context",
        AsyncMock(
            return_value=SimpleNamespace(
                tenant_id="t1", tenant_role="admin", ensure_role=lambda *args: None
            )
        ),
    )

    response = await router.get_conversation_messages(
        conversation_id="c123",
        request=_dummy_request(),
        current_user={"user_id": "u1"},
        tenant_id_header=None,
        tenant_role_header=None,
        limit=10,
        cursor=None,
        direction="desc",
    )

    assert stub.messages_called_with is not None
    conversation_id, kwargs = stub.messages_called_with
    assert conversation_id == "c123"
    assert kwargs["limit"] == 10
    assert response.items[0].content == "hello"
    assert response.next_cursor == "next-msg-cursor"
