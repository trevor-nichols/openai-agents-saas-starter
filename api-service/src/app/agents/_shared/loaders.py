"""Helpers for loading agent specs, prompts, and build order."""

from __future__ import annotations

import textwrap
from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from pathlib import Path

from app.agents._shared.specs import AgentSpec


def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def resolve_prompt(spec: AgentSpec) -> str:
    spec.ensure_prompt()
    if spec.instructions:
        return textwrap.dedent(spec.instructions).strip()
    if spec.prompt_path:
        return load_prompt(spec.prompt_path)
    raise ValueError(f"Agent '{spec.key}' is missing prompt content")


def topological_agent_order(specs: Sequence[AgentSpec]) -> list[str]:
    """Return agent keys in an order that respects handoff dependencies."""

    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)

    for spec in specs:
        deps = tuple(spec.handoff_keys) + tuple(getattr(spec, "agent_tool_keys", ()))
        for dep in deps:
            outgoing[dep].add(spec.key)
            incoming[spec.key].add(dep)
        incoming.setdefault(spec.key, set())
        outgoing.setdefault(spec.key, set())

    queue = deque([key for key, deps in incoming.items() if not deps])
    order: list[str] = []

    while queue:
        key = queue.popleft()
        order.append(key)
        for child in sorted(outgoing[key]):
            incoming[child].discard(key)
            if not incoming[child]:
                queue.append(child)

    if len(order) != len(incoming):
        missing = set(incoming) - set(order)
        cycle_hint = ", ".join(sorted(missing))
        raise ValueError(f"Cycle detected in agent handoffs: {cycle_hint}")

    return order


def default_agent_key(specs: Iterable[AgentSpec]) -> str:
    defaults = [spec.key for spec in specs if spec.default]
    if len(defaults) > 1:
        raise ValueError(f"Multiple default agents configured: {', '.join(sorted(defaults))}")
    if defaults:
        return defaults[0]
    # fallback: deterministic alphabetical
    sorted_specs = sorted(specs, key=lambda s: s.key)
    if not sorted_specs:
        raise ValueError("No agent specs configured")
    return sorted_specs[0].key


__all__ = ["resolve_prompt", "topological_agent_order", "default_agent_key", "load_prompt"]
