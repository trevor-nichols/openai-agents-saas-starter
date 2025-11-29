from __future__ import annotations

import pytest
from datetime import datetime

from app.domain.conversations import ConversationEvent
from app.services.conversation_service import conversation_service


@pytest.mark.asyncio
async def test_transcript_mode_filters_non_transcript_events():
    repo = conversation_service.repository
    events = [
        ConversationEvent(
            run_item_type="assistant_message",
            content_text="hello",
            sequence_no=0,
            timestamp=datetime.utcnow(),
        ),
        ConversationEvent(
            run_item_type="tool_result",
            content_text="tool output",
            sequence_no=1,
            timestamp=datetime.utcnow(),
        ),
        ConversationEvent(
            run_item_type="mcp_call",
            content_text="mcp",
            sequence_no=2,
            timestamp=datetime.utcnow(),
        ),
    ]

    await repo.add_run_events("conv-1", tenant_id="tenant-1", events=events)

    transcript_events = await conversation_service.get_run_events(
        "conv-1", tenant_id="tenant-1", include_types={
            "user_message",
            "assistant_message",
            "system_message",
            "tool_result",
        }
    )

    assert len(transcript_events) == 2
    assert {ev.run_item_type for ev in transcript_events} == {
        "assistant_message",
        "tool_result",
    }


@pytest.mark.asyncio
async def test_full_mode_returns_all_events_in_order():
    repo = conversation_service.repository
    events = [
        ConversationEvent(
            run_item_type="assistant_message",
            content_text="hello",
            sequence_no=0,
            timestamp=datetime.utcnow(),
        ),
        ConversationEvent(
            run_item_type="tool_result",
            content_text="tool output",
            sequence_no=1,
            timestamp=datetime.utcnow(),
        ),
        ConversationEvent(
            run_item_type="mcp_call",
            content_text="mcp",
            sequence_no=2,
            timestamp=datetime.utcnow(),
        ),
    ]

    await repo.add_run_events("conv-2", tenant_id="tenant-1", events=events)

    all_events = await conversation_service.get_run_events(
        "conv-2", tenant_id="tenant-1", include_types=None
    )

    assert [ev.sequence_no for ev in all_events] == [0, 1, 2]
    assert [ev.run_item_type for ev in all_events] == [
        "assistant_message",
        "tool_result",
        "mcp_call",
    ]
