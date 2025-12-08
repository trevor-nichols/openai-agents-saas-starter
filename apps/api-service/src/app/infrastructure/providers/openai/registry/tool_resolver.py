"""Tool selection and validation for OpenAI agents.

Separated from the registry facade to keep concerns focused and testable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from agents import CodeInterpreterTool, FileSearchTool, ImageGenerationTool, WebSearchTool

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.guardrails._shared.specs import AgentGuardrailConfig, ToolGuardrailConfig
from app.utils.tools import ToolRegistry
from openai.types.responses.tool_param import (
    CodeInterpreter,
    CodeInterpreterContainerCodeInterpreterToolAuto,
)

logger = logging.getLogger(__name__)
OPTIONAL_TOOL_KEYS: frozenset[str] = frozenset({"web_search"})


@dataclass(slots=True)
class ToolSelectionResult:
    tools: list[Any]
    code_interpreter_mode: str | None


class ToolResolver:
    """Resolves declarative tool keys into concrete SDK tool instances."""

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        settings_factory: Callable[[], Settings],
        guardrail_builder: Any | None = None,
    ):
        self._tool_registry = tool_registry
        self._settings_factory = settings_factory
        self._guardrail_builder = guardrail_builder

    def select_tools(
        self,
        spec: AgentSpec,
        *,
        runtime_ctx: PromptRuntimeContext | None,
        allow_unresolved_file_search: bool = False,
    ) -> ToolSelectionResult:
        settings = self._settings_factory()
        tool_keys = getattr(spec, "tool_keys", ()) or ()
        tool_configs = getattr(spec, "tool_configs", {}) or {}

        tools: list[Any] = []
        missing_required: list[str] = []
        missing_optional: list[str] = []
        code_mode: str | None = None

        global_tool_guardrails: ToolGuardrailConfig | None = getattr(
            spec, "tool_guardrails", None
        )
        per_tool_overrides: dict[str, ToolGuardrailConfig] = getattr(
            spec, "tool_guardrail_overrides", {}
        ) or {}

        for name in tool_keys:
            tool = self._tool_registry.get_tool(name)
            if tool is None:
                if name in OPTIONAL_TOOL_KEYS:
                    missing_optional.append(name)
                else:
                    missing_required.append(name)
                continue

            if isinstance(tool, CodeInterpreterTool):
                resolved_tool, code_mode = self._resolve_code_interpreter(
                    spec=spec,
                    tool_configs=tool_configs,
                    runtime_ctx=runtime_ctx,
                    settings=settings,
                )
                tools.append(resolved_tool)
            elif isinstance(tool, FileSearchTool):
                resolved = self._resolve_file_search_config(
                    spec=spec,
                    runtime_ctx=runtime_ctx,
                    settings=settings,
                    allow_unresolved=allow_unresolved_file_search,
                )
                tools.append(FileSearchTool(**resolved))
            elif isinstance(tool, ImageGenerationTool):
                base_cfg = dict(getattr(tool, "tool_config", {}) or {})
                override = tool_configs.get("image_generation", {})
                merged = {**base_cfg, **override}
                validated = self._validate_image_config(merged, settings)
                tools.append(ImageGenerationTool(tool_config=cast(Any, validated)))
            else:
                tools.append(tool)

            # Attach tool-level guardrails if configured
            try:
                self._attach_tool_guardrails(
                    tool=tools[-1],
                    tool_name=name,
                    global_config=global_tool_guardrails,
                    override_config=per_tool_overrides.get(name),
                )
            except Exception:
                logger.exception(
                    "tool.guardrails.attach_failed", extra={"tool": name, "agent": spec.key}
                )

        if missing_required:
            raise ValueError(
                f"Agent '{spec.key}' declares tool_keys {tool_keys} but these tools are "
                f"not registered: {', '.join(missing_required)}"
            )
        if missing_optional:
            logger.warning(
                "tools.missing_optional_for_agent",
                extra={"agent": spec.key, "missing_tools": missing_optional},
            )

        if runtime_ctx and runtime_ctx.user_location:
            tools = self._apply_user_location(tools, runtime_ctx)

        return ToolSelectionResult(tools=tools, code_interpreter_mode=code_mode)

    def _resolve_code_interpreter(
        self,
        *,
        spec: AgentSpec,
        tool_configs: dict[str, Any],
        runtime_ctx: PromptRuntimeContext | None,
        settings: Settings,
    ) -> tuple[CodeInterpreterTool, str]:
        config = tool_configs.get("code_interpreter", {})
        mode = config.get("mode", "auto")
        memory_limit = config.get("memory_limit") or settings.container_default_auto_memory
        file_ids = config.get("file_ids")

        container_id: str | None = None
        if runtime_ctx and runtime_ctx.container_bindings:
            container_id = runtime_ctx.container_bindings.get(spec.key)
        if config.get("container_id"):
            container_id = config.get("container_id")

        if mode == "explicit" and not container_id:
            if not settings.container_fallback_to_auto_on_missing_binding:
                raise ValueError(
                    f"Agent '{spec.key}' requires explicit code interpreter container "
                    "but none is bound"
                )

        if container_id:
            tool_config: CodeInterpreter = cast(
                CodeInterpreter,
                {"type": "code_interpreter", "container": container_id},
            )
            return CodeInterpreterTool(tool_config=tool_config), "explicit"

        auto_container = cast(
            CodeInterpreterContainerCodeInterpreterToolAuto,
            {"type": "auto", "memory_limit": memory_limit},
        )
        if file_ids:
            auto_container = cast(
                CodeInterpreterContainerCodeInterpreterToolAuto,
                {"type": "auto", "memory_limit": memory_limit, "file_ids": file_ids},
            )
        tool_config = cast(
            CodeInterpreter,
            {"type": "code_interpreter", "container": auto_container},
        )
        return CodeInterpreterTool(tool_config=tool_config), "auto"

    def _resolve_file_search_config(
        self,
        *,
        spec: AgentSpec,
        runtime_ctx: PromptRuntimeContext | None,
        settings: Settings,
        allow_unresolved: bool = False,
    ) -> dict[str, Any]:
        if runtime_ctx is None or runtime_ctx.file_search is None:
            if allow_unresolved:
                logger.warning(
                    "file_search runtime_ctx_missing during bootstrap; deferring vector_store_ids",
                    extra={"agent": spec.key},
                )
                return {"vector_store_ids": []}
            raise ValueError(
                "Agent '"
                + spec.key
                + "' requires file_search context but no vector_store_ids were provided"
            )

        resolved = (runtime_ctx.file_search or {}).get(spec.key)
        if not resolved:
            if allow_unresolved:
                logger.warning(
                    "file_search context missing for agent; skipping file_search tool",
                    extra={"agent": spec.key},
                )
                return {"vector_store_ids": []}
            raise ValueError(
                f"Agent '{spec.key}' requires file_search resolution but no "
                "vector_store_ids were provided"
            )

        vector_store_ids = resolved.get("vector_store_ids") or []
        if not vector_store_ids:
            raise ValueError(
                f"Agent '{spec.key}' file_search tool has no vector_store_ids for tenant context"
            )

        options = resolved.get("options") or {}
        allowed_keys = {"max_num_results", "filters", "ranking_options", "include_search_results"}
        cfg = {k: v for k, v in options.items() if k in allowed_keys}
        cfg["vector_store_ids"] = list(vector_store_ids)
        return cfg

    @staticmethod
    def _validate_image_config(config: dict[str, Any], settings: Settings) -> dict[str, Any]:
        allowed_sizes = {"auto", "1024x1024", "1024x1536", "1536x1024"}
        allowed_quality = {"auto", "low", "medium", "high"}
        allowed_background = {"auto", "opaque", "transparent"}
        allowed_formats = set(settings.image_allowed_formats)

        cfg = dict(config or {})
        if "format" in cfg and "output_format" not in cfg:
            cfg["output_format"] = cfg.pop("format")
        if "compression" in cfg and "output_compression" not in cfg:
            cfg["output_compression"] = cfg.pop("compression")

        cfg.setdefault("type", "image_generation")
        cfg.setdefault("size", settings.image_default_size)
        cfg.setdefault("quality", settings.image_default_quality)
        cfg.setdefault("output_format", settings.image_default_format)
        cfg.setdefault("background", settings.image_default_background)

        if cfg.get("size") not in allowed_sizes:
            raise ValueError(f"Unsupported image size '{cfg.get('size')}'")
        if cfg.get("quality") not in allowed_quality:
            raise ValueError(f"Unsupported image quality '{cfg.get('quality')}'")
        if cfg.get("background") not in allowed_background:
            raise ValueError(f"Unsupported image background '{cfg.get('background')}'")
        if cfg.get("output_format") not in allowed_formats:
            raise ValueError(f"Unsupported image format '{cfg.get('output_format')}'")
        compression = cfg.get("output_compression")
        if compression is not None:
            if not isinstance(compression, int) or compression < 0 or compression > 100:
                raise ValueError("image_generation output_compression must be 0-100 or omitted")
        partial_images = cfg.get("partial_images")
        if partial_images is not None:
            if not isinstance(partial_images, int) or partial_images < 0:
                raise ValueError("partial_images must be a non-negative integer")
            if partial_images > settings.image_max_partial_images:
                raise ValueError(
                    f"partial_images must be between 0 and {settings.image_max_partial_images}"
                )
        return cfg

    @staticmethod
    def _apply_user_location(tools: list[Any], runtime_ctx: PromptRuntimeContext) -> list[Any]:
        customized: list[Any] = []
        for tool in tools:
            if isinstance(tool, WebSearchTool):
                customized.append(
                    WebSearchTool(
                        user_location=runtime_ctx.user_location,
                        filters=tool.filters,
                        search_context_size=tool.search_context_size,
                    )
                )
            else:
                customized.append(tool)
        return customized

    def _attach_tool_guardrails(
        self,
        *,
        tool: Any,
        tool_name: str,
        global_config: ToolGuardrailConfig | None,
        override_config: ToolGuardrailConfig | None,
    ) -> None:
        """Attach tool-level guardrails to a tool instance."""
        if self._guardrail_builder is None:
            return

        effective_config = self._resolve_tool_guardrail_config(
            global_config=global_config, override_config=override_config
        )
        if effective_config is None or effective_config.is_empty():
            return

        input_cfg: AgentGuardrailConfig | None = effective_config.input
        output_cfg: AgentGuardrailConfig | None = effective_config.output

        if input_cfg:
            tool_input_guardrails = self._guardrail_builder.build_tool_input_guardrails(input_cfg)
            if tool_input_guardrails:
                tool.tool_input_guardrails = tool_input_guardrails

        if output_cfg:
            tool_output_guardrails = self._guardrail_builder.build_tool_output_guardrails(
                output_cfg
            )
            if tool_output_guardrails:
                tool.tool_output_guardrails = tool_output_guardrails

    @staticmethod
    def _resolve_tool_guardrail_config(
        *,
        global_config: ToolGuardrailConfig | None,
        override_config: ToolGuardrailConfig | None,
    ) -> ToolGuardrailConfig | None:
        """Resolve the effective tool guardrail config for a specific tool."""
        if override_config is not None:
            if not override_config.enabled or override_config.is_empty():
                return None
            return override_config

        if global_config is None or global_config.is_empty() or not global_config.enabled:
            return None

        return global_config


__all__ = ["ToolResolver", "ToolSelectionResult", "OPTIONAL_TOOL_KEYS"]
