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
        # Uses web search, file search, and code interpreter for richer tests/flows.
        tool_keys=("web_search", "file_search", "code_interpreter"),
        # Bind to the tenant's primary store by default; callers can override via
        # context.vector_store_id(s).
        vector_store_binding="tenant_default",
        # Encourage citations by requesting search results from file_search.
        file_search_options={
            "max_num_results": 5,
            "include_search_results": True,
        },
        prompt_path=base_dir / "prompt.md.j2",
        prompt_context_keys=("user", "tenant", "agent", "run", "env"),
    )
