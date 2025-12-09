from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="pdf_designer",
        display_name="PDF Designer",
        description="Designs and renders concise PDFs using Code Interpreter.",
        model_key="code",
        capabilities=("design", "code", "documents"),
        tool_keys=("code_interpreter",),
        tool_configs={
            "code_interpreter": {
                "mode": "auto",
                "memory_limit": "4g",
            }
        },
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
        # Default to trim history if this agent ever receives handoffs.
        handoff_context={},
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 6,
            "token_budget": 32000,
        },
    )
