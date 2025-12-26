from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from tests.utils.stream_assertions import (
    assert_code_interpreter_expectations,
    assert_file_search_expectations,
    assert_function_tool_expectations,
    assert_agent_tool_stream_expectations,
    assert_handoff_expectations,
    assert_image_generation_expectations,
    assert_mcp_tool_expectations,
    assert_memory_checkpoint_expectations,
    assert_provider_error_expectations,
    assert_reasoning_summary_expectations,
    assert_refusal_expectations,
    assert_web_search_expectations,
    assert_workflow_expectations,
    load_stream_fixture,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
BASE = REPO_ROOT / "docs" / "contracts" / "public-sse-streaming" / "examples"


@pytest.mark.contract
@pytest.mark.parametrize(
    "fixture_name,assert_fn,kwargs",
    [
        ("chat-web-search.ndjson", assert_web_search_expectations, {}),
        ("chat-code-interpreter.ndjson", assert_code_interpreter_expectations, {}),
        ("chat-file-search.ndjson", assert_file_search_expectations, {"expected_store_id": "vs_primary"}),
        ("chat-function-tool.ndjson", assert_function_tool_expectations, {}),
        ("chat-agent-tool-streaming.ndjson", assert_agent_tool_stream_expectations, {}),
        ("chat-image-generation-partials.ndjson", assert_image_generation_expectations, {}),
        ("chat-handoff.ndjson", assert_handoff_expectations, {"expected_from": "triage", "expected_to": "structured"}),
        ("chat-mcp-tool.ndjson", assert_mcp_tool_expectations, {}),
        ("chat-refusal.ndjson", assert_refusal_expectations, {}),
        ("chat-reasoning-summary.ndjson", assert_reasoning_summary_expectations, {}),
        ("chat-memory-checkpoint.ndjson", assert_memory_checkpoint_expectations, {}),
        ("chat-provider-error.ndjson", assert_provider_error_expectations, {}),
        (
            "workflow-analysis-code.ndjson",
            assert_workflow_expectations,
            {"expected_workflow_key": "analysis_code", "expected_steps": {"analysis", "code"}},
        ),
    ],
)
def test_stream_goldens(
    fixture_name: str, assert_fn: Callable[..., None], kwargs: dict[str, object]
):
    path = BASE / fixture_name
    if not path.exists():
        pytest.skip(f"Fixture missing: {path}")

    events = load_stream_fixture(path)
    assert_fn(events, **kwargs)
