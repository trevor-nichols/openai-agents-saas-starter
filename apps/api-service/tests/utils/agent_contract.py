"""Test helpers for stable agent API contracts.

These utilities derive expectations from on-disk AgentSpec declarations.
Contract tests should assert invariants against these computed values rather
than hard-coding tool sets or schema types that evolve with agent redesigns.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.agents._shared.registry_loader import load_agent_specs


@lru_cache(maxsize=1)
def spec_index():
    """Return a cached mapping of agent_key -> AgentSpec."""

    return {spec.key: spec for spec in load_agent_specs()}


def default_agent_key() -> str:
    """Return the currently configured default agent key."""

    for spec in spec_index().values():
        if getattr(spec, "default", False):
            return spec.key
    # Fall back to the first spec if no explicit default is set.
    return next(iter(spec_index().keys()))


def schema_agent_key() -> str:
    """Return a representative agent key that declares json_schema output."""

    for spec in spec_index().values():
        output = getattr(spec, "output", None)
        if output and getattr(output, "mode", None) == "json_schema":
            return spec.key
    raise AssertionError("No agent declares json_schema output; tests require one schema-capable agent.")


def expected_output_schema(agent_key: str) -> dict[str, Any] | None:
    """Compute the JSON schema expected for an agent, if configured."""

    from app.services.agents.output_schema import resolve_output_schema

    spec = spec_index().get(agent_key)
    if spec is None:
        raise KeyError(f"Unknown agent spec '{agent_key}'")
    return resolve_output_schema(spec)


def expected_tools_by_agent() -> dict[str, set[str]]:
    """Compute per-agent tooling from specs."""

    result: dict[str, set[str]] = {}
    for key, spec in spec_index().items():
        tools = tuple(getattr(spec, "tool_keys", ()) or ()) + tuple(
            getattr(spec, "agent_tool_keys", ()) or ()
        )
        result[key] = set(tools)
    return result


__all__ = [
    "spec_index",
    "default_agent_key",
    "schema_agent_key",
    "expected_output_schema",
    "expected_tools_by_agent",
]

