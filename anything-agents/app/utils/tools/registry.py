# File: app/utils/tools/registry.py
# Purpose: Tool registry for managing and organizing agent tools
# Dependencies: typing, functools
# Used by: Agent service for centralized tool management

from typing import List, Dict, Any, Callable, Optional, Union
from functools import lru_cache

# =============================================================================
# TOOL REGISTRY CLASS
# =============================================================================

class ToolRegistry:
    """
    Central registry for managing agent tools.
    
    This class provides a clean, extensible way to manage tools across
    all agents while maintaining separation of concerns.
    """
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}  # Changed to Any to handle FunctionTool objects
        self._tool_categories: Dict[str, List[str]] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(
        self,
        tool_func: Union[Callable, Any],  # Accept both functions and FunctionTool objects
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a tool function.
        
        Args:
            tool_func: The tool function to register (function or FunctionTool object)
            category: Tool category for organization
            metadata: Optional metadata about the tool
        """
        # Handle both regular functions and FunctionTool objects
        if hasattr(tool_func, 'name'):
            # This is a FunctionTool object from OpenAI Agents SDK
            tool_name = tool_func.name
        elif hasattr(tool_func, '__name__'):
            # This is a regular function
            tool_name = tool_func.__name__
        else:
            raise ValueError(f"Cannot determine name for tool: {tool_func}")
        
        # Register the tool
        self._tools[tool_name] = tool_func
        
        # Add to category
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        self._tool_categories[category].append(tool_name)
        
        # Store metadata
        self._tool_metadata[tool_name] = metadata or {}
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        return self._tools.get(tool_name)
    
    def get_tools_by_category(self, category: str) -> List[Any]:
        """Get all tools in a specific category."""
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_all_tools(self) -> List[Any]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_core_tools(self) -> List[Any]:
        """
        Get core tools that should be available to all agents.
        
        Returns:
            List[Any]: List of core tool functions/objects
        """
        # For now, return all tools. In the future, you could filter by metadata
        return self.get_all_tools()
    
    def get_specialized_tools(self, agent_type: str) -> List[Any]:
        """
        Get specialized tools for a specific agent type.
        
        Args:
            agent_type: Type of agent (e.g., "code_assistant", "data_analyst")
            
        Returns:
            List[Any]: List of specialized tools for the agent
        """
        # This can be extended to return agent-specific tools
        # For now, return empty list since we only have core tools
        return []
    
    def list_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """Get list of all tool categories."""
        return list(self._tool_categories.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Optional[Dict[str, Any]]: Tool information including metadata
        """
        if tool_name not in self._tools:
            return None
        
        tool_func = self._tools[tool_name]
        metadata = self._tool_metadata.get(tool_name, {})
        
        # Handle both regular functions and FunctionTool objects
        if hasattr(tool_func, 'description'):
            # FunctionTool object
            docstring = tool_func.description
        elif hasattr(tool_func, '__doc__'):
            # Regular function
            docstring = tool_func.__doc__
        else:
            docstring = None
        
        return {
            "name": tool_name,
            "function": tool_func,
            "docstring": docstring,
            "metadata": metadata,
            "category": self._get_tool_category(tool_name)
        }
    
    def _get_tool_category(self, tool_name: str) -> Optional[str]:
        """Get the category of a specific tool."""
        for category, tools in self._tool_categories.items():
            if tool_name in tools:
                return category
        return None

# =============================================================================
# GLOBAL REGISTRY INSTANCE
# =============================================================================

@lru_cache()
def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Uses LRU cache to ensure single instance across the application.
    
    Returns:
        ToolRegistry: Global tool registry instance
    """
    return ToolRegistry()

# =============================================================================
# INITIALIZATION FUNCTION
# =============================================================================

def initialize_tools() -> ToolRegistry:
    """
    Initialize and populate the tool registry with available tools.
    
    This function should be called during application startup to register
    all available tools.
    
    Returns:
        ToolRegistry: Populated tool registry
    """
    registry = get_tool_registry()
    
    # Import and register tools
    try:
        from .web_search import tavily_search_tool
        
        registry.register_tool(
            tavily_search_tool,
            category="web_search",
            metadata={
                "description": "Search the web for current information using Tavily API",
                "requires_api_key": True,
                "api_service": "tavily"
            }
        )
    except ImportError as e:
        print(f"Warning: Could not import web search tools: {e}")
    
    return registry 