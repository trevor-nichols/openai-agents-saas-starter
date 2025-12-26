"""Unit tests for agent tooling flag helpers."""

from app.services.agents.tooling import (
    normalize_tool_overview,
    resolve_tooling_by_agent,
    resolve_tooling_flags,
)


def test_resolve_tooling_flags() -> None:
    flags = resolve_tooling_flags(["code_interpreter", "file_search"])
    assert flags["supports_code_interpreter"] is True
    assert flags["supports_file_search"] is True
    assert flags["supports_image_generation"] is False
    assert flags["supports_web_search"] is False


def test_resolve_tooling_by_agent() -> None:
    tooling = resolve_tooling_by_agent({"agent-a": ["web_search"]})
    assert tooling["agent-a"]["supports_web_search"] is True
    assert tooling["agent-a"]["supports_code_interpreter"] is False


def test_normalize_tool_overview_handles_shapes() -> None:
    overview = {
        "per_agent": {
            "agent-a": ["code_interpreter"],
            "agent-b": "file_search",
            "agent-c": {"unexpected": "shape"},
        }
    }
    normalized = normalize_tool_overview(overview)
    assert normalized["agent-a"] == ["code_interpreter"]
    assert normalized["agent-b"] == ["file_search"]
    assert normalized["agent-c"] == []
