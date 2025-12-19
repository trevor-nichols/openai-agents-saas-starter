from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec, AgentToolConfig


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="director",
        display_name="Task Director",
        description="Directs work by delegating to specialist agent-tools.",
        model_key=None,
        capabilities=("orchestrator", "delegation", "tools"),
        tool_keys=("get_current_time", "search_conversations"),
        agent_tool_keys=(
            "retriever",
            "pdf_designer",
            "code_assistant",
            "researcher",
            "image_studio",
        ),
        agent_tool_overrides={
            "retriever": AgentToolConfig(
                tool_name="retrieve_knowledge",
                tool_description="Grounded answers from tenant docs with citations.",
                max_turns=6,
            ),
            "pdf_designer": AgentToolConfig(
                tool_name="generate_pdf",
                tool_description="Designs and renders concise, branded PDFs.",
                max_turns=8,
            ),
            "code_assistant": AgentToolConfig(
                tool_name="code_helper",
                tool_description="Solves coding tasks, small refactors, and reviews.",
                max_turns=6,
            ),
            "researcher": AgentToolConfig(
                tool_name="research_deepdive",
                tool_description="Performs grounded research with citations.",
                max_turns=6,
                custom_output_extractor="app.agents._shared.extractors.final_answer_only",
            ),
            "image_studio": AgentToolConfig(
                tool_name="image_creator",
                tool_description="Generates images with safe defaults and style control.",
                max_turns=4,
            ),
        },
        prompt_path=base_dir / "prompt.md.j2",
        # Keep history lean for tool-style workflows.
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 8,
            "token_budget": 32000,
        },
    )
