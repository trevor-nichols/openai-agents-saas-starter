# File: app/utils/tools/registry.py
# Purpose: Tool registry for managing and organizing agent tools
# Dependencies: typing, functools
# Used by: Agent service for centralized tool management

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from functools import lru_cache
from typing import Any

from agents import WebSearchTool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Inventory of tools available to agents (no implicit inclusion)."""

    def __init__(self):
        self._tools: dict[str, Any] = {}
        self._tool_categories: dict[str, list[str]] = {}
        self._tool_metadata: dict[str, dict[str, Any]] = {}

    def register_tool(
        self,
        tool_func: Callable[..., Any] | Any,  # function or SDK tool object
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool with a stable name (taken from SDK .name or function __name__)."""

        if hasattr(tool_func, "name"):
            tool_name = tool_func.name
        elif hasattr(tool_func, "__name__"):
            tool_name = tool_func.__name__
        else:
            raise ValueError(f"Cannot determine name for tool: {tool_func}")

        self._tools[tool_name] = tool_func
        self._tool_metadata[tool_name] = dict(metadata or {})

        if category not in self._tool_categories:
            self._tool_categories[category] = []
        if tool_name not in self._tool_categories[category]:
            self._tool_categories[category].append(tool_name)

    def get_tool(self, tool_name: str) -> Any | None:
        return self._tools.get(tool_name)

    def resolve_tools(
        self, tool_names: Iterable[str], *, ignore_missing: bool = False
    ) -> list[Any]:
        missing: list[str] = []
        resolved: list[Any] = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool is None:
                missing.append(name)
            else:
                resolved.append(tool)
        if missing and not ignore_missing:
            raise ValueError(f"Requested tools not registered: {', '.join(missing)}")
        return resolved

    def list_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def list_categories(self) -> list[str]:
        return list(self._tool_categories.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        if tool_name not in self._tools:
            return None

        tool_func = self._tools[tool_name]
        metadata = self._tool_metadata.get(tool_name, {})

        if hasattr(tool_func, "description"):
            docstring = tool_func.description
        elif hasattr(tool_func, "__doc__"):
            docstring = tool_func.__doc__
        else:
            docstring = None

        return {
            "name": tool_name,
            "function": tool_func,
            "docstring": docstring,
            "metadata": metadata,
            "category": self._get_tool_category(tool_name),
        }

    def _get_tool_category(self, tool_name: str) -> str | None:
        for category, tools in self._tool_categories.items():
            if tool_name in tools:
                return category
        return None


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

    # Hosted web search (OpenAI)
    settings = get_settings()
    if settings.openai_api_key and settings.openai_api_key.strip():
        registry.register_tool(
            WebSearchTool(),
            category="web_search",
            metadata={
                "description": (
                    "Search the web for current information using OpenAI hosted web search."
                ),
                "provider": "openai",
            },
        )
    else:
        logger.info(
            "OPENAI_API_KEY is not configured; hosted web search tool will be disabled.",
            extra={"provider": "openai"},
        )

    return registry
