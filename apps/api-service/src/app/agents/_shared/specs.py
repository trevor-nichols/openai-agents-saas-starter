"""Agent specification primitives used to declare agents declaratively.

Each agent provides a lightweight `AgentSpec` that describes its key, model,
prompt source, capabilities, and handoff targets. Providers turn these specs
into concrete SDK `Agent` objects at startup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.guardrails._shared.specs import AgentGuardrailConfig, ToolGuardrailConfig


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Declarative description of an agent entrypoint.

    - `key` is the stable identifier used in APIs and handoffs.
    - `display_name` is a human-friendly label.
    - `description` is shown in catalogs (e.g., `/api/v1/agents`).
    - `model_key` controls which settings override is applied (e.g., "triage"
      resolves to `settings.agent_triage_model`). If unset, `agent_default_model`
      is used.
    - `capabilities` describe the agent for catalog/filtering; tool selection
      is now explicit via `tool_keys`.
    - `instructions` or `prompt_path` provide the system prompt. Only one is
      required; `prompt_path` is preferred for long prompts.
    - `handoff_keys` lists other agent keys this agent can delegate to.
    - `default` marks the default agent for the provider.
    - `wrap_with_handoff_prompt` optionally passes the prompt through the SDK
      handoff helper to prepend handoff instructions (useful for orchestrators).
    - `tool_keys` is the ordered set of tool identifiers that will be attached
      to the concrete Agent instance (no implicit/default/core tools).
    - `handoff_context` optionally overrides how much history is forwarded to a
      specific handoff target ("full" = default, "fresh" = no history, "last_turn"
      = trim to most recent turn or two). This mirrors the SDK handoff
      `input_filter` without forcing every agent to re-implement it.
    - `handoff_overrides` allows per-target tool metadata and filters (see HandoffConfig).
    - `agent_tool_keys` lists agent keys that should be exposed as tools on this
      agent (caller retains control; different from handoffs which transfer control).
    - `agent_tool_overrides` allows per-agent-tool metadata (see AgentToolConfig).
    - `vector_store_binding` and `vector_store_ids` control how file_search resolves
      vector stores (tenant_default vs static ids).
    - `file_search_options` are passed through to the FileSearchTool (e.g.,
      max_num_results, filters, ranking_options, include_search_results).
    - `guardrails` specifies input/output guardrails configuration (preset key,
      explicit guardrail configs, or both). See AgentGuardrailConfig for details.
    - `tool_guardrails` applies guardrails to all tools on this agent (tool_input
      and tool_output stages). Per-tool overrides can disable or replace these.
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
    # Explicit tool assignment (mirrors Agents SDK: Agent(..., tools=[...])).
    tool_keys: tuple[str, ...] = ()
    # Optional per-tool configuration (e.g., {"code_interpreter": {"mode": "explicit"}}).
    tool_configs: dict[str, Any] = field(default_factory=dict)
    # Optional per-handoff context policy keyed by target agent key. Values:
    # - "full" (default): pass entire history
    # - "fresh": start with an empty history for the target agent
    # - "last_turn": keep only the most recent turn(s)
    handoff_context: dict[str, Literal["full", "fresh", "last_turn"]] = field(
        default_factory=dict
    )
    # Fine-grained per-target handoff metadata.
    handoff_overrides: dict[str, HandoffConfig] = field(default_factory=dict)
    # Optional agent-as-tool configuration.
    agent_tool_keys: tuple[str, ...] = ()
    agent_tool_overrides: dict[str, AgentToolConfig] = field(default_factory=dict)
    # Optional structured output configuration (maps to Agents SDK output_type).
    output: OutputSpec | None = None
    # File search / retrieval binding
    vector_store_binding: Literal["tenant_default", "static", "required"] = "tenant_default"
    vector_store_ids: tuple[str, ...] = ()
    file_search_options: dict[str, Any] = field(default_factory=dict)
    # Optional memory strategy defaults applied at agent level (resolved after per-request
    # and conversation overrides).
    memory_strategy: dict[str, Any] | None = None
    # Optional guardrails configuration for input/output validation.
    guardrails: AgentGuardrailConfig | None = None
    # Optional guardrails for all tools on this agent.
    tool_guardrails: ToolGuardrailConfig | None = None
    # Optional per-tool guardrail overrides keyed by tool name.
    tool_guardrail_overrides: dict[str, ToolGuardrailConfig] = field(default_factory=dict)

    def prompt_source(self) -> str:
        if self.instructions:
            return "instructions"
        if self.prompt_path:
            return "prompt_path"
        return ""

    def ensure_prompt(self) -> None:
        if not (self.instructions or self.prompt_path):
            raise ValueError(f"Agent '{self.key}' must supply instructions or prompt_path")


@dataclass(frozen=True, slots=True)
class AgentToolConfig:
    """Optional per-agent-as-tool customization.

    - tool_name/tool_description: overrides for the wrapped tool surface.
    - custom_output_extractor: dotted path to async callable (RunResult -> str).
    - is_enabled: optionally hide/show tool at runtime (bool or dotted callable path).
    - run_config: dict of RunConfig kwargs to pass through to as_tool.
    - max_turns: override the child agent's max turns when run as a tool.
    """

    tool_name: str | None = None
    tool_description: str | None = None
    custom_output_extractor: str | None = None
    is_enabled: bool | str | None = None
    run_config: dict[str, Any] | None = None
    max_turns: int | None = None


__all__ = ["AgentSpec", "HandoffConfig", "OutputSpec", "AgentToolConfig"]


@dataclass(frozen=True, slots=True)
class OutputSpec:
    """Declarative structured-output configuration for an agent.

    - mode: "text" leaves output as free-form text.
    - type_path: dotted import path to a Pydantic model / dataclass to use with AgentOutputSchema.
    - strict: whether to request strict JSON schema adherence (Structured Outputs). Defaults True.
    - custom_schema_path: dotted path to a subclass of AgentOutputSchemaBase when a bespoke schema
      or validation flow is needed (takes precedence over type_path).
    """

    mode: Literal["text", "json_schema"] = "text"
    type_path: str | None = None
    strict: bool = True
    custom_schema_path: str | None = None
@dataclass(frozen=True, slots=True)
class HandoffConfig:
    """Optional per-target handoff customization."""

    tool_name: str | None = None
    tool_description: str | None = None
    input_filter: str | None = None  # maps to registry-defined filter
    input_type: str | None = None  # dotted path to a pydantic/BaseModel type
    is_enabled: bool | None = None
