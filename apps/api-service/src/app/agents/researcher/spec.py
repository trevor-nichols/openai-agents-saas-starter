from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="researcher",
        display_name="Researcher",
        description="Conducts research with web grounding and synthesizes findings.",
        model_key="data",
        capabilities=("research", "search"),
        tool_keys=("web_search",),
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
    )
