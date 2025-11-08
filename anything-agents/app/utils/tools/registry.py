# File: app/utils/tools/registry.py
# Purpose: Tool registry for managing and organizing agent tools
# Dependencies: typing, functools
# Used by: Agent service for centralized tool management

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

# =============================================================================
# TOOL REGISTRY CLASS
# =============================================================================


@dataclass(slots=True)
class ToolAudience:
    """Normalized targeting metadata describing who can use a tool."""

    core: bool = True
    agents: frozenset[str] = field(default_factory=frozenset)
    capabilities: frozenset[str] = field(default_factory=frozenset)


class ToolRegistry:
    """
    Central registry for managing agent tools.

    This class provides a clean, extensible way to manage tools across
    all agents while maintaining separation of concerns.
    """

    def __init__(self):
        self._tools: dict[str, Any] = {}  # Store registered tool objects
        self._tool_categories: dict[str, list[str]] = {}
        self._tool_metadata: dict[str, dict[str, Any]] = {}
        self._tool_audience: dict[str, ToolAudience] = {}

    def register_tool(
        self,
        tool_func: Callable[..., Any] | Any,  # Accept both functions and FunctionTool objects
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a tool function.

        Args:
            tool_func: The tool function to register (function or FunctionTool object)
            category: Tool category for organization
            metadata: Optional metadata about the tool
        """
        # Handle both regular functions and FunctionTool objects
        if hasattr(tool_func, "name"):
            # This is a FunctionTool object from OpenAI Agents SDK
            tool_name = tool_func.name
        elif hasattr(tool_func, "__name__"):
            # This is a regular function
            tool_name = tool_func.__name__
        else:
            raise ValueError(f"Cannot determine name for tool: {tool_func}")

        # Register the tool
        self._tools[tool_name] = tool_func

        normalized_metadata = self._normalize_metadata(metadata)
        self._tool_metadata[tool_name] = normalized_metadata
        self._tool_audience[tool_name] = self._audience_from_metadata(normalized_metadata)

        # Add to category
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        if tool_name not in self._tool_categories[category]:
            self._tool_categories[category].append(tool_name)

    def get_tool(self, tool_name: str) -> Any | None:
        """Get a specific tool by name."""
        return self._tools.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[Any]:
        """Get all tools in a specific category."""
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_all_tools(self) -> list[Any]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_core_tools(self) -> list[Any]:
        """Return tools marked as `core` (shared across all agents)."""

        return [
            self._tools[name] for name, audience in self._tool_audience.items() if audience.core
        ]

    def get_tools_for_agent(
        self,
        agent_name: str,
        *,
        capabilities: Iterable[str] | None = None,
        include_core: bool = True,
    ) -> list[Any]:
        """Return the subset of tools that the given agent is allowed to use."""

        normalized_agent = agent_name.strip().lower()
        capability_set = {
            value.strip().lower() for value in (capabilities or []) if value and value.strip()
        }

        selected: list[Any] = []
        for name, tool in self._tools.items():
            audience = self._tool_audience.get(name)
            if audience is None:
                audience = ToolAudience()
                self._tool_audience[name] = audience

            if include_core and audience.core:
                selected.append(tool)
                continue

            if normalized_agent and normalized_agent in audience.agents:
                selected.append(tool)
                continue

            if capability_set and capability_set.intersection(audience.capabilities):
                selected.append(tool)

        return selected

    def get_specialized_tools(self, agent_type: str) -> list[Any]:
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

    def list_tool_names(self) -> list[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def list_categories(self) -> list[str]:
        """Get list of all tool categories."""
        return list(self._tool_categories.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
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
        audience = self._tool_audience.get(tool_name, ToolAudience())

        # Handle both regular functions and FunctionTool objects
        if hasattr(tool_func, "description"):
            # FunctionTool object
            docstring = tool_func.description
        elif hasattr(tool_func, "__doc__"):
            # Regular function
            docstring = tool_func.__doc__
        else:
            docstring = None

        return {
            "name": tool_name,
            "function": tool_func,
            "docstring": docstring,
            "metadata": {
                **metadata,
                "core": audience.core,
                "agents": sorted(audience.agents),
                "capabilities": sorted(audience.capabilities),
            },
            "category": self._get_tool_category(tool_name),
        }

    def _get_tool_category(self, tool_name: str) -> str | None:
        """Get the category of a specific tool."""
        for category, tools in self._tool_categories.items():
            if tool_name in tools:
                return category
        return None

    # =============================================================================
    # GLOBAL REGISTRY INSTANCE
    # =============================================================================

    def _normalize_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any]:
        data = dict(metadata or {})

        agents = data.get("agents")
        data["agents"] = self._normalize_string_list(agents)

        capabilities = data.get("capabilities")
        data["capabilities"] = self._normalize_string_list(capabilities)

        if "core" not in data:
            data["core"] = True

        return data

    def _audience_from_metadata(self, metadata: dict[str, Any]) -> ToolAudience:
        return ToolAudience(
            core=bool(metadata.get("core", True)),
            agents=frozenset(value.lower() for value in metadata.get("agents", [])),
            capabilities=frozenset(value.lower() for value in metadata.get("capabilities", [])),
        )

    @staticmethod
    def _normalize_string_list(values: Any) -> list[str]:
        if not values:
            return []
        if isinstance(values, str):
            values_iterable: Iterable[str] = [values]
        else:
            values_iterable = values
        normalized: list[str] = []
        for item in values_iterable:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.append(text)
        return sorted(set(normalized))


@lru_cache
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
                "api_service": "tavily",
                "core": False,
                "agents": ["triage", "data_analyst"],
                "capabilities": ["web_search"],
            },
        )
    except ImportError as e:
        print(f"Warning: Could not import web search tools: {e}")

    return registry
