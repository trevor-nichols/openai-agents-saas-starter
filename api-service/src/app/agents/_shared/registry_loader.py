"""Discovery utilities for agent specs on disk."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path

from app.agents._shared.specs import AgentSpec

AGENTS_ROOT = Path(__file__).resolve().parent.parent


def discover_agent_modules(root: Path = AGENTS_ROOT) -> Sequence[tuple[str, str]]:
    """Return a list of (agent_key, module_path) under the agents directory."""

    modules: list[tuple[str, str]] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        module_path = f"app.agents.{path.name}.spec"
        modules.append((path.name, module_path))
    return modules


def load_agent_specs(root: Path = AGENTS_ROOT) -> list[AgentSpec]:
    specs: list[AgentSpec] = []
    for key, module_path in discover_agent_modules(root):
        module = importlib.import_module(module_path)
        factory = getattr(module, "get_agent_spec", None)
        if factory is None:
            raise ImportError(f"Agent module {module_path} must expose get_agent_spec()")
        spec = factory()
        if not isinstance(spec, AgentSpec):
            raise TypeError(f"{module_path}.get_agent_spec() must return AgentSpec")
        if spec.key != key:
            raise ValueError(
                f"Agent spec key '{spec.key}' does not match directory name '{key}'"
            )
        specs.append(spec)
    return specs


__all__ = ["load_agent_specs", "discover_agent_modules", "AGENTS_ROOT"]
