from __future__ import annotations

from pathlib import Path

from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    base_dir = Path(__file__).resolve().parent
    return AgentSpec(
        key="retriever",
        display_name="Knowledge Retriever",
        description=(
            "Answers with grounded evidence from tenant docs (vector store) and "
            "optional web fallback."
        ),
        model_key="data",
        capabilities=("rag", "search", "research"),
        tool_keys=("file_search", "web_search"),
        vector_store_binding="tenant_default",
        file_search_options={
            "max_num_results": 8,
            "include_search_results": True,
            "ranking_options": {"score_threshold": 0.4},
        },
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
        memory_strategy={
            "mode": "trim",
            "max_user_turns": 8,
            "token_budget": 32000,
        },
    )
