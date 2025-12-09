from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="image_studio",
        display_name="Image Studio",
        description="Generates images with clear prompts and safe defaults.",
        model_key=None,
        capabilities=("images", "creative"),
        tool_keys=("image_generation",),
        tool_configs={
            "image_generation": {
                "size": "1024x1024",
                "quality": "high",
                "partial_images": 0,
            }
        },
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 6,
            "token_budget": 24000,
        },
    )
