from __future__ import annotations

import json

from app.domain.ai.models import AgentRunUsage
from app.services.workflows.output import aggregate_usage, format_stream_output


def test_aggregate_usage_returns_none_when_empty():
    assert aggregate_usage([None, None]) is None


def test_aggregate_usage_sums_known_fields():
    usage = aggregate_usage(
        [
            AgentRunUsage(input_tokens=1, output_tokens=2, total_tokens=3, requests=1),
            AgentRunUsage(input_tokens=4, total_tokens=5, cached_input_tokens=2),
        ]
    )
    assert usage is not None
    assert usage.input_tokens == 5
    assert usage.output_tokens == 2
    assert usage.total_tokens == 8
    assert usage.cached_input_tokens == 2
    assert usage.requests == 1


def test_format_stream_output_handles_text_and_structured():
    text, structured = format_stream_output("hello")
    assert text == "hello"
    assert structured is None

    text, structured = format_stream_output({"a": 1})
    assert structured == {"a": 1}
    assert json.loads(text or "{}") == {"a": 1}
