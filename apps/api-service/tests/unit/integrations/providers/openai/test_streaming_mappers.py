from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.infrastructure.providers.openai.streaming import OpenAIStreamingHandle


def _make_handle(metadata: dict[str, object] | None = None):
    stream = SimpleNamespace(last_response_id="resp-1", context_wrapper=None)
    return OpenAIStreamingHandle(
        stream=stream,
        agent_key="triage",
        metadata=metadata or {},
        lifecycle_bus=None,
    )


def test_map_raw_response_event_sets_reasoning_delta_and_tool_call_file_search():
    handle = _make_handle()
    raw = SimpleNamespace(
        type="response.file_search_call.searching",
        sequence_number=3,
        item_id="fs-1",
    )
    event = SimpleNamespace(type="raw_response_event", data=raw)

    mapped = handle._map_raw_response_event(event)

    assert mapped.kind == "raw_response_event"
    assert mapped.sequence_number == 3
    assert mapped.tool_call is not None
    assert mapped.tool_call["tool_type"] == "file_search"
    assert mapped.tool_call["file_search_call"]["status"] == "searching"


def test_map_raw_response_event_code_interpreter_completed():
    handle = _make_handle({"code_interpreter_mode": "auto"})
    raw = SimpleNamespace(
        type="response.code_interpreter_call.completed",
        sequence_number=2,
        item_id="ci-1",
    )
    event = SimpleNamespace(type="raw_response_event", data=raw)

    mapped = handle._map_raw_response_event(event)

    assert mapped.tool_call is not None
    assert mapped.tool_call["tool_type"] == "code_interpreter"
    assert mapped.tool_call["code_interpreter_call"]["status"] == "completed"
    assert mapped.tool_call["code_interpreter_call"]["container_mode"] == "auto"


def test_map_run_item_event_image_generation_includes_result_and_tool_ids():
    handle = _make_handle()
    item = SimpleNamespace(
        type="image_generation_call",
        id="img-1",
        status="completed",
        result="imgdata",
    )
    event = SimpleNamespace(type="run_item_stream_event", item=item, name="image-gen")

    mapped = handle._map_run_item_event(event)

    assert mapped.kind == "run_item_stream_event"
    assert mapped.tool_call_id == "img-1"
    assert mapped.tool_call["tool_type"] == "image_generation"
    assert mapped.tool_call["image_generation_call"]["result"] == "imgdata"


@pytest.mark.asyncio
async def test_events_yields_lifecycle_then_final_output():
    # minimal end-to-end: stream with no events but final_output set
    class _Stream:
        def __init__(self):
            self.final_output = {"foo": "bar"}
            self.last_response_id = "resp-final"
            self.context_wrapper = None

        async def stream_events(self):
            if False:
                yield None

    handle = OpenAIStreamingHandle(
        stream=_Stream(),
        agent_key="triage",
        metadata={},
        lifecycle_bus=None,
    )

    events = []
    async for ev in handle.events():
        events.append(ev)

    assert events
    final = events[-1]
    assert final.is_terminal is True
    assert final.response_id == "resp-final"
    assert final.structured_output == {"foo": "bar"}
