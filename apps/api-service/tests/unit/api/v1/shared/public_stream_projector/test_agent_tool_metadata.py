from __future__ import annotations

from types import SimpleNamespace

from app.api.v1.shared.public_stream_projector import PublicStreamProjector
from app.api.v1.shared.streaming import CodeInterpreterTool, ToolStatusEvent
from app.domain.ai.models import AgentStreamEvent, StreamScope
from app.infrastructure.providers.openai.stream_event_mapper import map_stream_event


def test_agent_tool_status_includes_agent_from_metadata() -> None:
    projector = PublicStreamProjector(stream_id="test_stream")

    seed = AgentStreamEvent(
        kind="raw_response_event",
        raw_type="response.output_item.added",
        raw_event={
            "output_index": 0,
            "item": {
                "id": "call_agent_01",
                "type": "function_call",
                "name": "ask_researcher",
                "status": "in_progress",
            },
        },
    )
    projector.project(
        seed,
        conversation_id="conv-1",
        response_id="resp-1",
        agent="triage",
        workflow_meta=None,
        server_timestamp="2025-12-15T00:00:00Z",
    )

    tool_called = AgentStreamEvent(
        kind="run_item_stream_event",
        run_item_name="tool_called",
        run_item_type="function_call",
        tool_call_id="call_agent_01",
        tool_name="ask_researcher",
        payload={
            "raw_item": {
                "call_id": "call_agent_01",
                "type": "function_call",
                "name": "ask_researcher",
            }
        },
        metadata={
            "agent_tool_names": ["ask_researcher"],
            "agent_tool_name_map": {"ask_researcher": "Researcher"},
        },
    )

    events = projector.project(
        tool_called,
        conversation_id="conv-1",
        response_id="resp-1",
        agent="triage",
        workflow_meta=None,
        server_timestamp="2025-12-15T00:00:01Z",
    )

    status_events = [event for event in events if isinstance(event, ToolStatusEvent)]
    assert status_events, "Expected tool.status event for agent tool"
    tool_event = status_events[0]
    assert tool_event.tool.tool_type == "agent"
    assert tool_event.tool.agent == "Researcher"


def test_scoped_code_interpreter_status_includes_container_mode() -> None:
    raw_event = SimpleNamespace(
        type="response.code_interpreter_call.completed",
        sequence_number=7,
        item_id="ci-1",
        output_index=0,
    )
    stream_event = SimpleNamespace(type="raw_response_event", data=raw_event)

    mapped = map_stream_event(
        stream_event,
        response_id="resp-1",
        metadata={"code_interpreter_mode": "explicit"},
    )
    assert mapped is not None
    mapped.scope = StreamScope(
        type="agent_tool",
        tool_call_id="call_agent_01",
        tool_name="ask_researcher",
        agent="researcher",
    )

    projector = PublicStreamProjector(stream_id="test_stream")
    events = projector.project(
        mapped,
        conversation_id="conv-1",
        response_id="resp-1",
        agent="triage",
        workflow_meta=None,
        server_timestamp="2025-12-15T00:00:02Z",
    )

    code_tools: list[CodeInterpreterTool] = []
    for event in events:
        if isinstance(event, ToolStatusEvent) and isinstance(event.tool, CodeInterpreterTool):
            code_tools.append(event.tool)
    assert code_tools, "Expected code_interpreter tool.status event in scoped stream"
    assert code_tools[0].container_mode == "explicit"
