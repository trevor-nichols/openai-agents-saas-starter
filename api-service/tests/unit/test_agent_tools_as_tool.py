from agents import Agent

from app.agents._shared.specs import AgentSpec, AgentToolConfig
from app.infrastructure.providers.openai.registry import OpenAIAgentRegistry


def _dummy_registry_with_agent(agent_key: str, agent: Agent) -> OpenAIAgentRegistry:
    registry = OpenAIAgentRegistry.__new__(OpenAIAgentRegistry)
    # Minimal attributes required by _build_agent_tools
    registry._agents = {agent_key: agent}
    return registry


def test_agent_tool_uses_override_description_when_spec_missing():
    ext_agent = Agent(name="ext", instructions="do", handoff_description="handoff desc")
    spec = AgentSpec(
        key="orchestrator",
        display_name="Orchestrator",
        description="",
        agent_tool_keys=("ext",),
        agent_tool_overrides={
            "ext": AgentToolConfig(tool_name="ext_tool", tool_description="override desc")
        },
    )

    registry = _dummy_registry_with_agent("ext", ext_agent)
    tools = registry._build_agent_tools(
        spec=spec,
        spec_map={"orchestrator": spec},
        agents={},
        tools=[],
    )

    assert tools and tools[0].description == "override desc"


def test_agent_tool_uses_handoff_description_when_no_override_and_spec_missing():
    ext_agent = Agent(name="ext", instructions="do", handoff_description="handoff desc")
    spec = AgentSpec(
        key="orchestrator",
        display_name="Orchestrator",
        description="",
        agent_tool_keys=("ext",),
    )

    registry = _dummy_registry_with_agent("ext", ext_agent)
    tools = registry._build_agent_tools(
        spec=spec,
        spec_map={"orchestrator": spec},
        agents={},
        tools=[],
    )

    assert tools and tools[0].description == "handoff desc"
