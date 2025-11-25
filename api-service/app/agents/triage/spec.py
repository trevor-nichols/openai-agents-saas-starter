from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="triage",
        display_name="Triage Assistant",
        description="Primary triage assistant orchestrating handoffs.",
        model_key="triage",
        capabilities=("general", "search", "handoff"),
        tool_keys=("web_search", "get_current_time", "search_conversations"),
        prompt_path=base_dir / "prompt.md.j2",
        handoff_keys=("code_assistant", "data_analyst"),
        default=True,
        wrap_with_handoff_prompt=True,
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
        prompt_defaults={"user": {"name": "there"}},
    )
