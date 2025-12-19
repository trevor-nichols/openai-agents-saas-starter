from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec, OutputSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="company_intel",
        display_name="Company Intel Brief",
        description="Produces a structured company brief with sources.",
        model_key="data",
        capabilities=("research", "structured_output"),
        tool_keys=("web_search",),
        prompt_path=base_dir / "prompt.md.j2",
        output=OutputSpec(
            mode="json_schema",
            type_path="app.agents.company_intel.types.CompanyIntelBrief",
            strict=True,
        ),
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 8,
            "token_budget": 32000,
        },
    )
