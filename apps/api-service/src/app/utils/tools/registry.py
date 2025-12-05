# File: app/utils/tools/registry.py
# Purpose: Tool registry for managing and organizing agent tools
# Dependencies: typing, functools
# Used by: Agent service for centralized tool management

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from functools import lru_cache
from typing import Any, cast

from agents import (
    CodeInterpreterTool,
    FileSearchTool,
    HostedMCPTool,
    ImageGenerationTool,
    WebSearchTool,
)
from openai.types.responses.tool_param import (
    CodeInterpreter,
    CodeInterpreterContainerCodeInterpreterToolAuto,
)

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


class NamedHostedMCPTool(HostedMCPTool):
    """HostedMCPTool with caller-assigned name so multiple instances can coexist."""

    def __init__(
        self,
        *,
        name: str,
        tool_config: Any,
        on_approval_request: Callable[[Any], Any] | None = None,
    ):
        self._name_override = name
        super().__init__(tool_config=tool_config, on_approval_request=on_approval_request)

    @property
    def name(self) -> str:
        return self._name_override


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
        default_memory = settings.container_default_auto_memory or "1g"
        auto_container = cast(
            CodeInterpreterContainerCodeInterpreterToolAuto,
            {"type": "auto", "memory_limit": default_memory},
        )
        registry.register_tool(
            CodeInterpreterTool(
                tool_config=cast(
                    CodeInterpreter,
                    {"type": "code_interpreter", "container": auto_container},
                )
            ),
            category="code",
            metadata={
                "description": "Run Python in a sandboxed OpenAI container (auto-managed).",
                "mode": "auto",
                "default_memory": default_memory,
            },
        )

        image_config: dict[str, object] = {
            "type": "image_generation",
            "size": settings.image_default_size,
            "quality": settings.image_default_quality,
            "format": settings.image_default_format,
            "background": settings.image_default_background,
        }
        if settings.image_default_compression is not None:
            image_config["compression"] = settings.image_default_compression
        if settings.image_max_partial_images:
            image_config["partial_images"] = settings.image_max_partial_images

        registry.register_tool(
            ImageGenerationTool(tool_config=cast(Any, image_config)),
            category="image",
            metadata={
                "description": "Generate or edit images using OpenAI hosted image generation.",
                "provider": "openai",
                "defaults": image_config,
            },
        )
        registry.register_tool(
            FileSearchTool(vector_store_ids=[]),
            category="search",
            metadata={
                "description": "Search tenant vector stores (OpenAI hosted file_search).",
                "provider": "openai",
            },
        )
    else:
        logger.info(
            "OPENAI_API_KEY is not configured; hosted web search tool will be disabled.",
            extra={"provider": "openai"},
        )

    # Hosted MCP tools (OpenAI Responses API)
    if (getattr(settings, "mcp_tools", []) or []) and not (
        settings.openai_api_key and settings.openai_api_key.strip()
    ):
        logger.warning(
            "Hosted MCP tools configured but OPENAI_API_KEY is missing; skipping registration.",
            extra={"provider": "openai"},
        )
        return registry

    for mcp_cfg in getattr(settings, "mcp_tools", []) or []:
        tool_config: dict[str, Any] = {
            "type": "mcp",
            "server_label": mcp_cfg.server_label,
        }
        if mcp_cfg.server_url:
            tool_config["server_url"] = mcp_cfg.server_url
        if mcp_cfg.connector_id:
            tool_config["connector_id"] = mcp_cfg.connector_id
        if mcp_cfg.authorization:
            tool_config["authorization"] = mcp_cfg.authorization
        if mcp_cfg.require_approval:
            tool_config["require_approval"] = mcp_cfg.require_approval
        if mcp_cfg.allowed_tools:
            tool_config["allowed_tools"] = mcp_cfg.allowed_tools
        if mcp_cfg.description:
            tool_config["server_description"] = mcp_cfg.description

        def _build_approval_handler(cfg):
            allow = set(cfg.auto_approve_tools or [])
            deny = set(cfg.deny_tools or [])

            def _approve(request):
                tool_name = getattr(request.data, "name", None)
                if tool_name in deny:
                    return {"approve": False, "reason": "Denied by policy"}
                if tool_name in allow:
                    return {"approve": True}
                return {"approve": False, "reason": "Not auto-approved"}

            return _approve

        mcp_tool = NamedHostedMCPTool(
            name=mcp_cfg.name,
            tool_config=cast(Any, tool_config),
            on_approval_request=_build_approval_handler(mcp_cfg),
        )

        registry.register_tool(
            mcp_tool,
            category="mcp",
            metadata={
                "description": mcp_cfg.description or "Hosted MCP tool",
                "server_label": mcp_cfg.server_label,
                "server_url": mcp_cfg.server_url,
                "connector_id": mcp_cfg.connector_id,
            },
        )

    return registry
