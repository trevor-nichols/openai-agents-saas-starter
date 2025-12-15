from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.ai.lifecycle import LifecycleEventBus
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationAttachment
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.agents.streaming_pipeline import (
    AgentStreamProcessor,
    GuardrailStreamForwarder,
    build_guardrail_summary,
)


def test_build_guardrail_summary_counts_and_token_usage():
    summary = build_guardrail_summary(
        [
            {
                "guardrail_stage": "input",
                "guardrail_key": "x",
                "guardrail_tripwire_triggered": True,
                "guardrail_suppressed": False,
                "guardrail_token_usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            },
            {
                "guardrail_stage": "output",
                "guardrail_key": "x",
                "guardrail_tripwire_triggered": True,
                "guardrail_suppressed": True,
                "guardrail_token_usage": {"prompt_tokens": 4, "completion_tokens": 5, "total_tokens": 9},
            },
            {
                "guardrail_stage": "output",
                "guardrail_key": "y",
                "guardrail_tripwire_triggered": False,
            },
        ]
    )
    assert summary["total"] == 3
    assert summary["triggered"] == 2
    assert summary["suppressed"] == 1
    assert summary["by_key"] == {"x": 2, "y": 1}
    assert summary["by_stage"]["input"] == {"total": 1, "triggered": 1}
    assert summary["by_stage"]["output"] == {"total": 2, "triggered": 1}
    assert summary["token_usage"] == {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}


@pytest.mark.asyncio
async def test_guardrail_forwarder_emits_event_into_bus():
    bus = LifecycleEventBus()

    forwarder = GuardrailStreamForwarder(
        lifecycle_bus=bus,
        conversation_id="conv-1",
        default_agent="agent-1",
        get_current_agent=lambda: "agent-2",
        get_last_response_id=lambda: "resp-1",
        get_fallback_response_id=lambda: "resp-fallback",
    )
    forwarder(
        {
            "guardrail_stage": "input",
            "guardrail_key": "k1",
            "guardrail_name": "Test Guardrail",
            "guardrail_tripwire_triggered": True,
        }
    )

    # Allow the create_task() emission to run.
    await asyncio.sleep(0)
    emitted = [ev async for ev in bus.drain()]
    assert len(emitted) == 1
    assert emitted[0].kind == "guardrail_result"
    assert emitted[0].conversation_id == "conv-1"
    assert emitted[0].agent == "agent-2"
    assert emitted[0].response_id == "resp-1"
    assert emitted[0].guardrail_key == "k1"


@pytest.mark.asyncio
async def test_stream_processor_accumulates_response_and_attachments():
    bus = LifecycleEventBus()
    actor = ConversationActorContext(tenant_id="t1", user_id="u1")

    provider = SimpleNamespace(
        get_agent=lambda key: SimpleNamespace(output_schema={"type": "object"}) if key == "a2" else None
    )

    attachment_service = AttachmentService(lambda: None)  # storage is not used in this unit test
    attachment = ConversationAttachment(
        object_id="obj-1",
        filename="image.png",
        mime_type="image/png",
        size_bytes=10,
    )

    async def _ingest(tool_outputs, **_kwargs):
        return [attachment] if tool_outputs else []

    attachment_service.ingest_image_outputs = AsyncMock(side_effect=_ingest)

    processor = AgentStreamProcessor(
        lifecycle_bus=bus,
        provider=provider,
        actor=actor,
        conversation_id="conv-1",
        entrypoint_agent="a1",
        entrypoint_output_schema=None,
        attachment_service=attachment_service,
    )

    await bus.emit(AgentStreamEvent(kind="lifecycle", event="tool_start"))

    events = [
        AgentStreamEvent(
            kind="raw_response_event",
            text_delta="hi",
            payload={"type": "image_generation_call"},
        ),
        AgentStreamEvent(
            kind="agent_updated_stream_event",
            new_agent="a2",
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_text="hi",
            is_terminal=True,
        ),
    ]

    class _Handle:
        last_response_id = "resp-9"

        async def events(self):
            for ev in events:
                yield ev

    emitted = [ev async for ev in processor.iter_events(_Handle())]

    assert processor.outcome.complete_response == "hi"
    assert processor.outcome.handoff_count == 1
    assert processor.outcome.current_agent == "a2"
    assert processor.outcome.current_output_schema == {"type": "object"}
    assert processor.outcome.last_response_id == "resp-9"
    assert len(processor.outcome.attachments) == 1

    assert emitted[0].attachments is not None
    assert emitted[0].payload is not None
    assert emitted[0].payload.get("_attachment_note") == "stored"

    # Last event is a drained lifecycle event from the bus.
    assert emitted[-1].kind == "lifecycle"
