from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.agents.run_pipeline import (
    RunContext,
    persist_assistant_message,
    prepare_run_context,
    project_new_session_items,
    record_user_message,
)


class _FakeProvider:
    def __init__(self, *, name: str, descriptor) -> None:
        self.name = name
        self._descriptor = descriptor
        self.runtime = MagicMock()

    def resolve_agent(self, preferred_key=None):
        return self._descriptor


class _ProviderRegistry:
    def __init__(self, provider) -> None:
        self._provider = provider

    def get_default(self):
        return self._provider


@pytest.mark.asyncio
async def test_prepare_and_record_user_message_happy_path():
    descriptor = SimpleNamespace(
        key="triage", model="gpt", status="active", memory_strategy_defaults=None
    )
    provider = _FakeProvider(name="openai", descriptor=descriptor)
    registry = _ProviderRegistry(provider)

    interaction_builder = AsyncMock()
    interaction_builder.build.return_value = {"ctx": True}

    conversation_service = AsyncMock()
    conversation_service.get_session_state.return_value = None

    class _Handle:
        def get_items(self):
            return []

    session_manager = AsyncMock()
    session_manager.acquire_session.return_value = ("sess-1", _Handle())

    request = SimpleNamespace(
        message="hello",
        agent_type=None,
        conversation_id=None,
        memory_injection=None,
        memory_strategy=None,
    )
    actor = SimpleNamespace(tenant_id="t1", user_id="u1")

    ctx = await prepare_run_context(
        actor=actor,
        request=request,
        provider_registry=registry,
        interaction_builder=interaction_builder,
        conversation_service=conversation_service,
        session_manager=session_manager,
    )

    await record_user_message(ctx=ctx, request=request, conversation_service=conversation_service)

    conversation_service.append_message.assert_called_once()
    _, _, kwargs = conversation_service.append_message.mock_calls[0]
    assert kwargs["metadata"].agent_entrypoint == "triage"
    assert kwargs["metadata"].sdk_session_id == "sess-1"


@pytest.mark.asyncio
async def test_persist_assistant_message_happy_path():
    conversation_service = AsyncMock()
    ctx = RunContext(
        actor=SimpleNamespace(tenant_id="t1", user_id="u1"),
        provider=SimpleNamespace(name="openai"),
        descriptor=SimpleNamespace(key="triage", model="gpt"),
        conversation_id="conv-1",
        session_id="sess-1",
        session_handle=None,
        provider_conversation_id=None,
        runtime_ctx={},
        pre_session_items=[],
        existing_state=None,
    )

    await persist_assistant_message(
        ctx=ctx,
        conversation_service=conversation_service,
        response_text="hi",
        attachments=[],
    )

    conversation_service.append_message.assert_called_once()
    _, _, kwargs = conversation_service.append_message.mock_calls[0]
    assert kwargs["metadata"].active_agent == "triage"


@pytest.mark.asyncio
async def test_project_new_session_items_best_effort_on_failure():
    class DummyHandle:
        def get_items(self):
            return [
                {"id": "pre"},
                {"id": "post"},
            ]

    failing_projector = AsyncMock()
    failing_projector.ingest_session_items.side_effect = RuntimeError("boom")

    # Should swallow errors
    await project_new_session_items(
        event_projector=failing_projector,
        session_handle=DummyHandle(),
        pre_items=[{"id": "pre"}],
        conversation_id="conv-1",
        tenant_id="tenant-1",
        agent="triage",
        model="gpt-5.1",
        response_id="resp-1",
    )

    failing_projector.ingest_session_items.assert_called_once()


@pytest.mark.asyncio
async def test_project_new_session_items_handles_strategy_rewrite():
    pre_items = [
        {"id": "u1", "type": "message", "role": "user"},
        {"id": "a1", "type": "message", "role": "assistant"},
        {"id": "a2", "type": "message", "role": "assistant"},
    ]
    post_items = [
        {"id": "a2", "type": "message", "role": "assistant"},  # kept
        {"id": "n1", "type": "message", "role": "assistant", "content": "new"},
    ]

    class DummyHandle:
        def get_items(self):
            return post_items

    projector = AsyncMock()

    await project_new_session_items(
        event_projector=projector,
        session_handle=DummyHandle(),
        pre_items=pre_items,
        conversation_id="conv-1",
        tenant_id="tenant-1",
        agent="triage",
        model="gpt-5.1",
        response_id="resp-1",
    )

    projector.ingest_session_items.assert_called_once()
    _, _, kwargs = projector.ingest_session_items.mock_calls[0]
    assert kwargs["session_items"] == [post_items[1]]


@pytest.mark.asyncio
async def test_project_new_session_items_detects_rewritten_item_content():
    pre_items = [{"id": "x1", "type": "message", "content": "old"}]
    post_items = [
        {"id": "x1", "type": "message", "content": "new"},  # rewritten
        {"id": "n2", "type": "message", "content": "newer"},
    ]

    class DummyHandle:
        def get_items(self):
            return post_items

    projector = AsyncMock()

    await project_new_session_items(
        event_projector=projector,
        session_handle=DummyHandle(),
        pre_items=pre_items,
        conversation_id="conv-1",
        tenant_id="tenant-1",
        agent="triage",
        model="gpt-5.1",
        response_id="resp-1",
    )

    projector.ingest_session_items.assert_called_once()
    _, _, kwargs = projector.ingest_session_items.mock_calls[0]
    assert kwargs["session_items"] == post_items
