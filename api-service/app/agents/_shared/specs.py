"""Agent specification primitives used to declare agents declaratively.

Each agent provides a lightweight `AgentSpec` that describes its key, model,
prompt source, capabilities, and handoff targets. Providers turn these specs
into concrete SDK `Agent` objects at startup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Declarative description of an agent entrypoint.

    - `key` is the stable identifier used in APIs and handoffs.
    - `display_name` is a human-friendly label.
    - `description` is shown in catalogs (e.g., `/api/v1/agents`).
    - `model_key` controls which settings override is applied (e.g., "triage"
      resolves to `settings.agent_triage_model`). If unset, `agent_default_model`
      is used.
    - `capabilities` are used for tool selection; they map to tool metadata
      and replace the old global capability map.
    - `instructions` or `prompt_path` provide the system prompt. Only one is
      required; `prompt_path` is preferred for long prompts.
    - `handoff_keys` lists other agent keys this agent can delegate to.
    - `default` marks the default agent for the provider.
    - `wrap_with_handoff_prompt` optionally passes the prompt through the SDK
      handoff helper to prepend handoff instructions (useful for orchestrators).
    """

    key: str
    display_name: str
    description: str
    model_key: str | None = None
    capabilities: tuple[str, ...] = ()
    instructions: str | None = None
    prompt_path: Path | None = None
    handoff_keys: tuple[str, ...] = ()
    default: bool = False
    wrap_with_handoff_prompt: bool = False
    prompt_context_keys: tuple[str, ...] = ()
    prompt_defaults: dict[str, Any] = field(default_factory=dict)
    extra_context_providers: tuple[str, ...] = ()

    def prompt_source(self) -> str:
        if self.instructions:
            return "instructions"
        if self.prompt_path:
            return "prompt_path"
        return ""

    def ensure_prompt(self) -> None:
        if not (self.instructions or self.prompt_path):
            raise ValueError(f"Agent '{self.key}' must supply instructions or prompt_path")


__all__ = ["AgentSpec"]
