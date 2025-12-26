from types import SimpleNamespace
from typing import cast

from agents import Agent

from app.agents._shared.specs import AgentSpec, AgentToolConfig
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry.agent_builder import AgentBuilder
from app.infrastructure.providers.openai.registry.prompt import PromptRenderer
from app.infrastructure.providers.openai.registry.tool_resolver import ToolResolver
from app.utils.tools import ToolRegistry


def _builder_with_agent(agent_key: str, agent: Agent) -> tuple[AgentBuilder, dict[str, Agent]]:
    settings = SimpleNamespace(agent_default_model="gpt-5.1")
    settings_factory = lambda: cast(Settings, settings)  # noqa: E731
    tool_resolver = ToolResolver(tool_registry=ToolRegistry(), settings_factory=settings_factory)
    prompt_renderer = PromptRenderer(settings_factory=settings_factory)
    builder = AgentBuilder(
        tool_resolver=tool_resolver,
        prompt_renderer=prompt_renderer,
        settings_factory=settings_factory,
    )
    static_agents = {agent_key: agent}
    return builder, static_agents


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

    builder, static_agents = _builder_with_agent("ext", ext_agent)
    tools, _ = builder._build_agent_tools(  # noqa: SLF001
        spec=spec,
        spec_map={"orchestrator": spec},
        agents={},
        tools=[],
        static_agents=static_agents,
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

    builder, static_agents = _builder_with_agent("ext", ext_agent)
    tools, _ = builder._build_agent_tools(  # noqa: SLF001
        spec=spec,
        spec_map={"orchestrator": spec},
        agents={},
        tools=[],
        static_agents=static_agents,
    )

    assert tools and tools[0].description == "handoff desc"
