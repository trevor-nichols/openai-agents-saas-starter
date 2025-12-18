from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentGuardrailConfig, AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="compliance_reviewer",
        display_name="Compliance Reviewer",
        description="Checks content for safety/policy issues and suggests safe rewrites.",
        model_key=None,
        capabilities=("compliance", "safety"),
        tool_keys=(),
        guardrails=AgentGuardrailConfig(preset="strict"),
        prompt_path=base_dir / "prompt.md.j2",
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 6,
            "token_budget": 20000,
        },
    )
