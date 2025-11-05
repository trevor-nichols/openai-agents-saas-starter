# File: tests/test_tools.py
# Purpose: Test cases for agent tools functionality
# Dependencies: pytest, app/utils/tools
# Used by: Test suite for validating tool integration

from unittest.mock import Mock, patch

from app.utils.tools import get_tool_registry, initialize_tools
from app.utils.tools.web_search import get_tavily_client, tavily_search_tool

# =============================================================================
# TOOL REGISTRY TESTS
# =============================================================================

def test_tool_registry_initialization():
    """Test that the tool registry initializes correctly."""
    registry = get_tool_registry()
    
    assert registry is not None
    assert hasattr(registry, 'register_tool')
    assert hasattr(registry, 'get_all_tools')
    assert hasattr(registry, 'get_core_tools')

def test_initialize_tools():
    """Test that tools are properly initialized and registered."""
    registry = initialize_tools()
    
    # Check that tools are registered
    tool_names = registry.list_tool_names()
    assert 'tavily_search_tool' in tool_names
    
    # Check categories
    categories = registry.list_categories()
    assert 'web_search' in categories

def test_tool_registry_get_core_tools():
    """Test getting core tools from registry."""
    registry = initialize_tools()
    core_tools = registry.get_core_tools()
    
    assert len(core_tools) > 0
    # Check that we have the tavily search tool
    tool_names = [
        getattr(tool, "name", getattr(tool, "__name__", str(tool)))
        for tool in core_tools
    ]
    assert "tavily_search_tool" in tool_names

# =============================================================================
# WEB SEARCH TOOL TESTS
# =============================================================================

def test_tavily_search_tool_is_function_tool():
    """Test that tavily_search_tool is a proper FunctionTool object."""
    from agents.tool import FunctionTool
    
    assert isinstance(tavily_search_tool, FunctionTool)
    assert tavily_search_tool.name == 'tavily_search_tool'
    assert tavily_search_tool.description is not None
    assert 'Search the web using Tavily API' in tavily_search_tool.description
    assert tavily_search_tool.params_json_schema is not None

def test_get_tavily_client_no_api_key():
    """Test getting Tavily client when no API key is configured."""
    with patch('app.utils.tools.web_search.get_settings') as mock_settings:
        mock_settings.return_value = Mock(spec=[])  # No tavily_api_key attribute
        
        client = get_tavily_client()
        assert client is None

def test_get_tavily_client_with_api_key():
    """Test getting Tavily client with API key configured."""
    with patch('app.utils.tools.web_search.get_settings') as mock_settings:
        mock_settings.return_value = Mock(tavily_api_key="test_key")
        
        with patch('app.utils.tools.web_search.TavilyClient') as mock_tavily:
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
    search_tool = registry.get_tool('tavily_search_tool')
    assert search_tool is not None
    # For FunctionTool objects, check the name attribute
    assert hasattr(search_tool, 'name') and search_tool.name == 'tavily_search_tool'
    
    # Test getting tools by category
    web_tools = registry.get_tools_by_category('web_search')
    assert len(web_tools) > 0
    # Check that we have the tavily search tool in web tools
    tool_names = [
        getattr(tool, "name", getattr(tool, "__name__", str(tool)))
        for tool in web_tools
    ]
    assert "tavily_search_tool" in tool_names
    
    # Test tool info
    tool_info = registry.get_tool_info('tavily_search_tool')
    assert tool_info is not None
    assert tool_info['name'] == 'tavily_search_tool'
    assert tool_info['category'] == 'web_search'
    assert 'metadata' in tool_info

def test_tool_can_be_used_by_agent():
    """Test that the tool can be properly used by an Agent."""
    from agents import Agent
    
    # Create an agent with the tavily search tool
    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent with web search capabilities.",
        tools=[tavily_search_tool]
    )
    
    # Verify the agent has the tool
    assert len(agent.tools) == 1
    assert agent.tools[0].name == 'tavily_search_tool'

def test_tool_registry_provides_tools_for_agents():
    """Test that the tool registry can provide tools for agent creation."""
    registry = initialize_tools()
    
    # Get tools for an agent
    core_tools = registry.get_core_tools()
    
    # Verify we can create an agent with these tools
    from agents import Agent
    
    agent = Agent(
        name="Test Agent",
        instructions="You are a test agent.",
        tools=core_tools
    )
    
    # Verify the agent has tools
    assert len(agent.tools) > 0
    # Verify at least one tool is the tavily search tool
    tool_names = [tool.name for tool in agent.tools]
    assert 'tavily_search_tool' in tool_names 
