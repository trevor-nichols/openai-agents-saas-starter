import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.chat.schemas import AgentChatRequest
from app.services.agent_service import AgentService
from app.services.agents.context import ConversationActorContext


@pytest.mark.asyncio
async def test_chat_starts_title_task_once(monkeypatch):
    calls: list[dict] = []

    async def fake_start_title_task(self, **kwargs):
        calls.append(kwargs)
        return None

    monkeypatch.setattr(AgentService, "_start_title_task", fake_start_title_task)

    # Stub dependencies used inside chat
    async def fake_record_user_message(**_kwargs):
        return None

    async def fake_persist_assistant_message(**_kwargs):
        return None

    async def fake_project_new_session_items(**_kwargs):
        return None

    monkeypatch.setattr(
        "app.services.agents.run_pipeline.record_user_message", fake_record_user_message
    )
    monkeypatch.setattr(
        "app.services.agents.run_pipeline.persist_assistant_message", fake_persist_assistant_message
    )
    monkeypatch.setattr(
        "app.services.agents.run_pipeline.project_new_session_items",
        fake_project_new_session_items,
    )

    # Stub prepare_run_context to avoid provider/DB wiring.
    class StubRuntime:
        async def run(self, *_args, **_kwargs):
            return SimpleNamespace(
                response_text="hello",
                final_output="hello",
                final_agent=None,
                handoff_count=0,
                tool_outputs=None,
                response_id="rid",
                usage=None,
            )

    class StubProvider:
        name = "provider"
        runtime = StubRuntime()

        def tool_overview(self):
            return {"tool_names": []}

        def mark_seen(self, *_args, **_kwargs):
            return None

    class StubDescriptor:
        key = "agent"
        model = "model"

    async def fake_prepare_run_context(*_args, **_kwargs):
        return SimpleNamespace(
            actor=ConversationActorContext(tenant_id="t", user_id="u"),
            provider=StubProvider(),
            descriptor=StubDescriptor(),
            conversation_id="c1",
            provider_conversation_id=None,
            session_handle=None,
            session_id="s1",
            runtime_ctx={},
            pre_session_items=[],
            existing_state=None,
        )

    monkeypatch.setattr(
        "app.services.agents.run_pipeline.prepare_run_context", fake_prepare_run_context
    )

    # Stub attachment service methods referenced in chat response assembly.
    dummy_attachment_service = SimpleNamespace(
        ingest_image_outputs=AsyncMock(return_value=[]),
        to_attachment_schema=lambda att: att,
        attachment_metadata_note=lambda _atts: {},
    )

    svc = AgentService(
        conversation_service=None,
        conversation_repository=None,
        storage_service=None,
        container_service=None,
        vector_store_service=None,
    )
    svc._attachment_service = dummy_attachment_service
    svc._sync_session_state = AsyncMock()
    svc._record_usage_metrics = AsyncMock()

    actor = ConversationActorContext(tenant_id="t", user_id="u")
    req = AgentChatRequest(message="hi there")

    await svc.chat(req, actor=actor)

    assert len(calls) == 1, "Title task should be started exactly once per chat call"
