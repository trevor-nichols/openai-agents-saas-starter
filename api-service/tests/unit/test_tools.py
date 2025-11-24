# File: tests/unit/test_tools.py
# Purpose: Validate tool registry wiring and hosted web search integration

from types import SimpleNamespace
from typing import cast

import pytest
from agents import Agent, WebSearchTool
from openai.types.responses.web_search_tool_param import UserLocation

from app.agents._shared.loaders import topological_agent_order
from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.registry_loader import load_agent_specs
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry import OpenAIAgentRegistry
from app.utils.tools import ToolRegistry, get_tool_registry, initialize_tools

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _reset_tool_registry():
    get_tool_registry.cache_clear()
    yield
    get_tool_registry.cache_clear()


@pytest.fixture(autouse=True)
def _web_search_settings(monkeypatch):
    """Ensure initialize_tools sees an OpenAI API key so web search registers."""

    settings = SimpleNamespace(openai_api_key="test-key")
    monkeypatch.setattr("app.utils.tools.registry.get_settings", lambda: settings)
    yield


# =============================================================================
# TOOL REGISTRY TESTS
# =============================================================================


def test_tool_registry_initialization():
    registry = get_tool_registry()

    assert registry is not None
    assert hasattr(registry, "register_tool")
    assert hasattr(registry, "get_all_tools")
    assert hasattr(registry, "get_core_tools")


def test_initialize_tools_registers_web_search():
    registry = initialize_tools()

    tool_names = registry.list_tool_names()
    assert "web_search" in tool_names

    categories = registry.list_categories()
    assert "web_search" in categories


def test_tool_registry_get_core_tools():
    registry = ToolRegistry()

    def core_tool():
        return "core"

    def scoped_tool():
        return "scoped"

    registry.register_tool(core_tool, metadata={"core": True})
    registry.register_tool(scoped_tool, metadata={"core": False, "agents": ["triage"]})

    core_tools = registry.get_core_tools()

    tool_names = {
        getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in core_tools
    }
    assert tool_names == {"core_tool"}


# =============================================================================
# WEB SEARCH TOOL TESTS
# =============================================================================


def test_web_search_tool_defaults():
    tool = WebSearchTool()

    assert tool.name == "web_search"
    assert tool.user_location is None
    assert tool.search_context_size == "medium"


def test_tool_registry_integration():
    registry = initialize_tools()

    search_tool = registry.get_tool("web_search")
    assert isinstance(search_tool, WebSearchTool)

    web_tools = registry.get_tools_by_category("web_search")
    tool_names = [getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in web_tools]
    assert "web_search" in tool_names

    tool_info = registry.get_tool_info("web_search")
    assert tool_info is not None
    assert tool_info["name"] == "web_search"
    assert tool_info["category"] == "web_search"
    assert "metadata" in tool_info
    assert tool_info["metadata"]["agents"] == ["data_analyst", "triage"]


def test_tool_can_be_used_by_agent():
    registry = initialize_tools()
    search_tool = registry.get_tool("web_search")
    assert search_tool is not None

    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent with web search capabilities.",
        tools=[search_tool],
    )

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "web_search"


async def _noop_search(*args, **kwargs):  # pragma: no cover - helper
    return []


def _build_openai_registry(monkeypatch, registry: ToolRegistry):
    class _StubSettings:
        agent_default_model: str = "gpt-5.1"
        agent_triage_model: str | None = None
        agent_code_model: str | None = None
        agent_data_model: str | None = None

    settings = _StubSettings()
    monkeypatch.setattr(
        "app.infrastructure.providers.openai.registry.initialize_tools",
        lambda: registry,
    )
    return OpenAIAgentRegistry(
        settings_factory=lambda: cast(Settings, settings),
        conversation_searcher=_noop_search,
    )


def test_tool_registry_provides_tools_for_agents(monkeypatch):
    registry = initialize_tools()
    _build_openai_registry(monkeypatch, registry)

    triage_tools = registry.get_tools_for_agent("triage")

    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent.",
        tools=triage_tools,
    )

    tool_names = [tool.name for tool in agent.tools]
    assert "web_search" in tool_names
    assert "get_current_time" in tool_names


def test_get_tools_for_agent_filters_by_metadata():
    registry = ToolRegistry()

    def core_tool():
        return "core"

    def code_tool():
        return "code"

    def data_tool():
        return "data"

    registry.register_tool(core_tool, metadata={"core": True})
    registry.register_tool(code_tool, metadata={"core": False, "agents": ["code_assistant"]})
    registry.register_tool(
        data_tool,
        metadata={
            "core": False,
            "capabilities": ["analysis"],
        },
    )

    code_tools = registry.get_tools_for_agent("code_assistant")
    data_tools = registry.get_tools_for_agent("data_analyst", capabilities=["analysis"])

    code_names = {
        getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in code_tools
    }
    data_names = {
        getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in data_tools
    }

    assert code_names == {"core_tool", "code_tool"}
    assert data_names == {"core_tool", "data_tool"}


def test_web_search_tool_applies_request_location(monkeypatch):
    registry = initialize_tools()
    openai_registry = _build_openai_registry(monkeypatch, registry)

    runtime_ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="conv-1",
        request_message="hi",
        settings=None,
        user_location=cast(UserLocation, {"type": "approximate", "city": "Austin"}),
    )

    agent = openai_registry.get_agent_handle(
        "triage", runtime_ctx=runtime_ctx, validate_prompts=False
    )
    assert agent is not None

    web_tool = next(tool for tool in agent.tools if isinstance(tool, WebSearchTool))
    assert web_tool.user_location == {"type": "approximate", "city": "Austin"}


def test_agent_specs_are_sorted_topologically():
    specs = load_agent_specs()
    order = topological_agent_order(specs)

    assert set(order) == {spec.key for spec in specs}
    assert order.index("triage") > order.index("code_assistant")
    assert order.index("triage") > order.index("data_analyst")
