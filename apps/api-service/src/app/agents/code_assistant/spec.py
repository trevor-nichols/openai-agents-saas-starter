from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="code_assistant",
        display_name="Code Assistant",
        description=(
            "Senior software engineer for code analysis, debugging, reviews, "
            "and implementation guidance. Has access to a sandboxed Python "
            "environment for data analysis and algorithm verification."
        ),
        model_key="code",
        capabilities=("code", "analysis", "debugging"),
        tool_keys=("code_interpreter",),
        prompt_path=base_dir / "prompt.md.j2",
        extra_context_providers=("timestamp",),
        memory_strategy={
            "mode": "compact",
            "max_user_turns": 10,
            "keep_last_user_turns": 2,
            "token_budget": 32000,
        },
    )
