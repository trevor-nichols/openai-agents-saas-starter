"""Derive UI-safe tooling flags from agent tool keys."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

_TOOL_FLAG_MAP: dict[str, str] = {
    "code_interpreter": "supports_code_interpreter",
    "file_search": "supports_file_search",
    "image_generation": "supports_image_generation",
    "web_search": "supports_web_search",
}


def resolve_tooling_flags(tool_keys: Iterable[str] | None) -> dict[str, bool]:
    """Return a stable set of tooling capability flags for UI consumers."""

    keys = {str(key) for key in (tool_keys or []) if key}
    return {flag: tool in keys for tool, flag in _TOOL_FLAG_MAP.items()}


def resolve_tooling_by_agent(
    per_agent: Mapping[str, Iterable[str]] | None
) -> dict[str, dict[str, bool]]:
    """Resolve tooling flags for each agent key."""

    result: dict[str, dict[str, bool]] = {}
    if not per_agent:
        return result
    for agent_key, tool_keys in per_agent.items():
        result[str(agent_key)] = resolve_tooling_flags(tool_keys)
    return result


def normalize_tool_overview(overview: Mapping[str, Any] | None) -> dict[str, list[str]]:
    """Extract per-agent tool names from provider tool_overview responses."""

    if not overview:
        return {}
    per_agent = overview.get("per_agent")
    if not isinstance(per_agent, Mapping):
        return {}
    normalized: dict[str, list[str]] = {}
    for agent_key, entry in per_agent.items():
        if isinstance(entry, list | tuple | set):
            normalized[str(agent_key)] = [str(value) for value in entry]
        elif isinstance(entry, str):
            normalized[str(agent_key)] = [entry]
        else:
            normalized[str(agent_key)] = []
    return normalized


__all__ = [
    "resolve_tooling_flags",
    "resolve_tooling_by_agent",
    "normalize_tool_overview",
]
