from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="code_assistant",
        display_name="Code Assistant",
        description="Handles software engineering questions and code reviews.",
        model_key="code",
        capabilities=("code", "search"),
        tool_keys=("code_interpreter",),
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
    )
