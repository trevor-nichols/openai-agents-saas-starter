from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="data_analyst",
        display_name="Data Analyst",
        description="Supports analytical and quantitative queries.",
        model_key="data",
        capabilities=("analysis", "search"),
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
    )
