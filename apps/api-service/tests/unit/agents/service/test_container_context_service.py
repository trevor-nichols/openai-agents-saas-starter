from __future__ import annotations

import pytest

from app.agents._shared.prompt_context import ContainerOverrideContext, PromptRuntimeContext
from app.agents._shared.specs import AgentSpec
from app.services.agents.container_context import ContainerContextService
from app.services.agents.context import ConversationActorContext


class _FakeConversationService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[object]]] = []

    async def append_run_events(self, conversation_id, *, tenant_id, events):
        self.calls.append((conversation_id, tenant_id, events))


@pytest.mark.asyncio
async def test_container_context_events_append():
    spec = AgentSpec(
        key="triage",
        display_name="Triage",
        description="",
        tool_keys=("code_interpreter",),
    )
    runtime_ctx = PromptRuntimeContext(
        actor=ConversationActorContext(tenant_id="tenant-1", user_id="user-1"),
        conversation_id="conv-1",
        request_message=None,
        settings={},
        container_overrides={
            "triage": ContainerOverrideContext(
                container_id="local-1",
                openai_container_id="openai-1",
            )
        },
    )

    service = ContainerContextService(spec_loader=lambda: [spec])
    fake_conversation = _FakeConversationService()

    await service.append_run_events(
        conversation_service=fake_conversation,
        conversation_id="conv-1",
        tenant_id="tenant-1",
        agent_keys=["triage"],
        runtime_ctx=runtime_ctx,
        response_id="resp-1",
    )

    assert fake_conversation.calls, "expected run events to be appended"
    _, _, events = fake_conversation.calls[0]
    event = events[0]
    assert event.run_item_type == "tool_context"
    assert event.run_item_name == "code_interpreter"
    assert event.call_output == {
        "container_context": {
            "source": "override",
            "container_id": "local-1",
            "openai_container_id": "openai-1",
        }
    }
