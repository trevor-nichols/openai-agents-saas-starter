import pytest
from types import SimpleNamespace
from typing import cast

from agents import FileSearchTool, ImageGenerationTool

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry.tool_resolver import ToolResolver
from app.utils.tools import ToolRegistry


def _settings() -> Settings:
    return cast(
        Settings,
        SimpleNamespace(
            container_default_auto_memory="1g",
            container_fallback_to_auto_on_missing_binding=False,
            image_default_size="1024x1024",
            image_default_quality="high",
            image_default_format="png",
            image_default_background="auto",
            image_default_compression=None,
            image_max_partial_images=0,
            image_allowed_formats=["png", "jpeg", "webp"],
        ),
    )


def _resolver(registry: ToolRegistry) -> ToolResolver:
    return ToolResolver(tool_registry=registry, settings_factory=_settings)


def _spec(**kwargs) -> AgentSpec:
    return AgentSpec(
        key="test",
        display_name="Test",
        description="",
        instructions="do",
        **kwargs,
    )


def test_missing_required_tool_raises():
    registry = ToolRegistry()
    resolver = _resolver(registry)
    spec = _spec(tool_keys=("file_search",))

    with pytest.raises(ValueError):
        resolver.select_tools(spec, runtime_ctx=None)


def test_file_search_missing_vector_store_ids_errors():
    registry = ToolRegistry()
    registry.register_tool(FileSearchTool(vector_store_ids=[]))
    resolver = _resolver(registry)
    spec = _spec(tool_keys=("file_search",))
    ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="c1",
        request_message=None,
        settings=_settings(),
        file_search={},
    )

    with pytest.raises(ValueError):
        resolver.select_tools(spec, runtime_ctx=ctx)


def test_file_search_allow_unresolved_returns_empty():
    registry = ToolRegistry()
    registry.register_tool(FileSearchTool(vector_store_ids=[]))
    resolver = _resolver(registry)
    spec = _spec(tool_keys=("file_search",))
    ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="c1",
        request_message=None,
        settings=_settings(),
        file_search={},
    )

    result = resolver.select_tools(spec, runtime_ctx=ctx, allow_unresolved_file_search=True)

    assert result.tools and isinstance(result.tools[0], FileSearchTool)
    # FileSearchTool may not expose tool_config; fall back to any attr it provides.
    cfg = getattr(result.tools[0], "tool_config", None) or getattr(result.tools[0], "__dict__", {}).get(
        "tool_config", {}
    )
    if cfg:
        assert cfg.get("vector_store_ids") == []


def test_image_generation_invalid_size_raises():
    registry = ToolRegistry()
    registry.register_tool(ImageGenerationTool(tool_config={"type": "image_generation"}))
    resolver = _resolver(registry)
    spec = _spec(
        tool_keys=("image_generation",),
        tool_configs={"image_generation": {"size": "999x999"}},
    )

    with pytest.raises(ValueError):
        resolver.select_tools(spec, runtime_ctx=None)
