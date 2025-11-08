# File: tests/test_tools.py
# Purpose: Test cases for agent tools functionality
# Dependencies: pytest, app/utils/tools
# Used by: Test suite for validating tool integration

from unittest.mock import Mock, call, create_autospec, patch

from app.services.agent_service import AgentRegistry
from app.utils.tools import ToolRegistry, get_tool_registry, initialize_tools
from app.utils.tools.web_search import get_tavily_client, tavily_search_tool

# =============================================================================
# TOOL REGISTRY TESTS
# =============================================================================


def test_tool_registry_initialization():
    """Test that the tool registry initializes correctly."""
    registry = get_tool_registry()

    assert registry is not None
    assert hasattr(registry, "register_tool")
    assert hasattr(registry, "get_all_tools")
    assert hasattr(registry, "get_core_tools")


def test_initialize_tools():
    """Test that tools are properly initialized and registered."""
    registry = initialize_tools()

    # Check that tools are registered
    tool_names = registry.list_tool_names()
    assert "tavily_search_tool" in tool_names

    # Check categories
    categories = registry.list_categories()
    assert "web_search" in categories


def test_tool_registry_get_core_tools():
    """Test that only tools flagged as core are returned."""

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


def test_tavily_search_tool_is_function_tool():
    """Test that tavily_search_tool is a proper FunctionTool object."""
    from agents.tool import FunctionTool

    assert isinstance(tavily_search_tool, FunctionTool)
    assert tavily_search_tool.name == "tavily_search_tool"
    assert tavily_search_tool.description is not None
    assert "Search the web using Tavily API" in tavily_search_tool.description
    assert tavily_search_tool.params_json_schema is not None


def test_get_tavily_client_no_api_key():
    """Test getting Tavily client when no API key is configured."""
    with patch("app.utils.tools.web_search.get_settings") as mock_settings:
        mock_settings.return_value = Mock(spec=[])  # No tavily_api_key attribute

        client = get_tavily_client()
        assert client is None


def test_get_tavily_client_with_api_key():
    """Test getting Tavily client with API key configured."""
    with patch("app.utils.tools.web_search.get_settings") as mock_settings:
        mock_settings.return_value = Mock(tavily_api_key="test_key")

        with patch("app.utils.tools.web_search.TavilyClient") as mock_tavily:
            mock_tavily.return_value = Mock()

            client = get_tavily_client()
            assert client is not None
            mock_tavily.assert_called_once_with(api_key="test_key")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_tool_registry_integration():
    """Test full tool registry integration."""
    registry = initialize_tools()

    # Test getting tool by name
    search_tool = registry.get_tool("tavily_search_tool")
    assert search_tool is not None
    # For FunctionTool objects, check the name attribute
    assert hasattr(search_tool, "name") and search_tool.name == "tavily_search_tool"

    # Test getting tools by category
    web_tools = registry.get_tools_by_category("web_search")
    assert len(web_tools) > 0
    # Check that we have the tavily search tool in web tools
    tool_names = [getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in web_tools]
    assert "tavily_search_tool" in tool_names

    # Test tool info
    tool_info = registry.get_tool_info("tavily_search_tool")
    assert tool_info is not None
    assert tool_info["name"] == "tavily_search_tool"
    assert tool_info["category"] == "web_search"
    assert "metadata" in tool_info


def test_tool_can_be_used_by_agent():
    """Test that the tool can be properly used by an Agent."""
    from agents import Agent

    # Create an agent with the tavily search tool
    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent with web search capabilities.",
        tools=[tavily_search_tool],
    )

    # Verify the agent has the tool
    assert len(agent.tools) == 1
    assert agent.tools[0].name == "tavily_search_tool"


def test_tool_registry_provides_tools_for_agents():
    """Test that the tool registry can provide tools for agent creation."""
    registry = initialize_tools()
    AgentRegistry(registry)

    triage_tools = registry.get_tools_for_agent("triage")

    from agents import Agent

    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent.",
        tools=triage_tools,
    )

    assert len(agent.tools) > 0
    tool_names = [tool.name for tool in agent.tools]
    assert "tavily_search_tool" in tool_names
    assert "get_current_time" in tool_names


def test_get_tools_for_agent_filters_by_metadata():
    """Registry returns only tools targeted to the requested agent/capabilities."""

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


def test_agent_registry_requests_scoped_tools():
    """AgentRegistry asks the ToolRegistry for scoped tool lists per agent."""

    tool_registry = create_autospec(ToolRegistry, instance=True)
    tool_registry.list_tool_names.return_value = []
    tool_registry.list_categories.return_value = []
    tool_registry.get_tools_for_agent.side_effect = lambda agent_name, **_: [f"{agent_name}_tool"]

    with (
        patch("app.services.agent_service.Agent") as agent_cls,
        patch("app.services.agent_service.handoff", side_effect=lambda agent: agent),
        patch(
            "app.services.agent_service.prompt_with_handoff_instructions",
            side_effect=lambda text: text,
        ),
    ):
        agent_cls.return_value = object()
        AgentRegistry(tool_registry)

    expected_calls = [
        call("triage", capabilities=AgentRegistry._AGENT_CAPABILITIES["triage"]),
        call(
            "code_assistant",
            capabilities=AgentRegistry._AGENT_CAPABILITIES["code_assistant"],
        ),
        call(
            "data_analyst",
            capabilities=AgentRegistry._AGENT_CAPABILITIES["data_analyst"],
        ),
    ]

    assert tool_registry.get_tools_for_agent.call_args_list[:3] == expected_calls
