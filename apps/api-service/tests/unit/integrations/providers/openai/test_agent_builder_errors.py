from types import SimpleNamespace
from typing import cast

import pytest

from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry.agent_builder import AgentBuilder
from app.infrastructure.providers.openai.registry.prompt import PromptRenderer
from app.infrastructure.providers.openai.registry.tool_resolver import ToolResolver
from app.utils.tools import ToolRegistry


def _settings() -> Settings:
    return cast(Settings, SimpleNamespace(agent_default_model="gpt-5.1"))


def _builder() -> AgentBuilder:
    registry = ToolRegistry()
    resolver = ToolResolver(tool_registry=registry, settings_factory=_settings)
    renderer = PromptRenderer(settings_factory=_settings)
    return AgentBuilder(tool_resolver=resolver, prompt_renderer=renderer, settings_factory=_settings)


def _spec(**kwargs) -> AgentSpec:
    return AgentSpec(
        key="orchestrator",
        display_name="Orchestrator",
        description="",
        instructions="do",
        **kwargs,
    )


def test_handoff_missing_target_raises():
    builder = _builder()
    spec = _spec(handoff_keys=("missing",))

    with pytest.raises(ValueError):
        builder.build_agent(
            spec=spec,
            runtime_ctx=None,
            agents={},
            spec_map={"orchestrator": spec},
            validate_prompts=False,
        )


def test_agent_tool_missing_target_raises():
    builder = _builder()
    spec = _spec(agent_tool_keys=("missing",))

    with pytest.raises(ValueError):
        builder.build_agent(
            spec=spec,
            runtime_ctx=None,
            agents={},
            spec_map={"orchestrator": spec},
            validate_prompts=False,
        )
