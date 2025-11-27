# File: tests/unit/test_tools.py
# Purpose: Validate tool registry wiring and hosted web search integration

from types import SimpleNamespace
from typing import Any, cast

import pytest
from agents import Agent, WebSearchTool
from agents.handoffs import HandoffInputData
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

    settings = SimpleNamespace(
        openai_api_key="test-key",
        container_default_auto_memory="1g",
        image_default_size="1024x1024",
        image_default_quality="high",
        image_default_format="png",
        image_default_background="auto",
        image_default_compression=None,
        image_max_partial_images=0,
    )
    monkeypatch.setattr("app.utils.tools.registry.get_settings", lambda: settings)
    yield


# =============================================================================
# TOOL REGISTRY TESTS
# =============================================================================


def test_tool_registry_initialization():
    registry = get_tool_registry()

    assert registry is not None
    assert hasattr(registry, "register_tool")
    assert hasattr(registry, "list_tool_names")


def test_initialize_tools_registers_web_search():
    registry = initialize_tools()

    tool_names = registry.list_tool_names()
    assert "web_search" in tool_names

    categories = registry.list_categories()
    assert "web_search" in categories


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

    tool_info = registry.get_tool_info("web_search")
    assert tool_info is not None
    assert tool_info["name"] == "web_search"
    assert tool_info["category"] == "web_search"
    assert "metadata" in tool_info
    assert "provider" in tool_info["metadata"]


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
        container_default_auto_memory: str | None = "1g"

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
    openai_registry = _build_openai_registry(monkeypatch, registry)

    agent = openai_registry.get_agent_handle("triage", validate_prompts=False)
    assert agent is not None

    tool_names = [tool.name for tool in agent.tools]
    assert tool_names == ["web_search", "get_current_time", "search_conversations"]


def test_resolve_tools_order_and_missing():
    registry = ToolRegistry()

    def a_tool():
        return "a"

    def b_tool():
        return "b"

    registry.register_tool(a_tool)
    registry.register_tool(b_tool)

    resolved = registry.resolve_tools(["a_tool", "b_tool"])
    assert [t.__name__ for t in resolved] == ["a_tool", "b_tool"]

    with pytest.raises(ValueError):
        registry.resolve_tools(["a_tool", "missing"], ignore_missing=False)

    resolved_missing_ok = registry.resolve_tools(["a_tool", "missing"], ignore_missing=True)
    assert [t.__name__ for t in resolved_missing_ok] == ["a_tool"]


def test_handoff_fresh_policy_preserves_payload(monkeypatch):
    registry = ToolRegistry()
    openai_registry = _build_openai_registry(monkeypatch, registry)
    input_filter = openai_registry._make_handoff_input_filter("fresh")
    assert input_filter is not None

    data = HandoffInputData(
        input_history="old_turn",
        pre_handoff_items=cast(tuple[Any, ...], ("pre",)),
        new_items=cast(tuple[Any, ...], ("payload",)),
    )

    filtered = input_filter(data)
    assert filtered.input_history == ()
    assert filtered.new_items == ("payload",)
    assert filtered.pre_handoff_items == ("pre",)


def test_select_tools_missing_required_raises(monkeypatch):
    registry = ToolRegistry()  # intentionally empty (no required tools)

    monkeypatch.setattr(
        "app.infrastructure.providers.openai.registry.initialize_tools", lambda: registry
    )
    # Skip registering built-in tools so required tool_keys stay missing.
    monkeypatch.setattr(
        "app.infrastructure.providers.openai.registry.OpenAIAgentRegistry._register_builtin_tools",
        lambda self: None,
    )

    with pytest.raises(ValueError):
        _build_openai_registry(monkeypatch, registry)


def test_select_tools_missing_optional_web_search(monkeypatch):
    registry = ToolRegistry()

    # Only register built-ins (added by _register_builtin_tools), skip web_search
    monkeypatch.setattr(
        "app.infrastructure.providers.openai.registry.initialize_tools", lambda: registry
    )

    openai_registry = _build_openai_registry(monkeypatch, registry)
    agent = openai_registry.get_agent_handle("triage", validate_prompts=False)
    assert agent is not None

    tool_names = [tool.name for tool in agent.tools]
    assert "web_search" not in tool_names
    assert set(tool_names) == {"get_current_time", "search_conversations"}


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
