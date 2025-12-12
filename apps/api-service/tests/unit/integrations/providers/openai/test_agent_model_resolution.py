from types import SimpleNamespace
from typing import cast

import pytest

from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry.agent_builder import AgentBuilder
from app.infrastructure.providers.openai.registry.prompt import PromptRenderer
from app.infrastructure.providers.openai.registry.tool_resolver import ToolResolver
from app.utils.tools import ToolRegistry


def _builder(settings: SimpleNamespace) -> AgentBuilder:
    settings_factory = lambda: cast(Settings, settings)  # noqa: E731
    registry = ToolRegistry()
    resolver = ToolResolver(tool_registry=registry, settings_factory=settings_factory)
    renderer = PromptRenderer(settings_factory=settings_factory)
    return AgentBuilder(tool_resolver=resolver, prompt_renderer=renderer, settings_factory=settings_factory)


def _spec(**kwargs) -> AgentSpec:
    return AgentSpec(
        key="orchestrator",
        display_name="Orchestrator",
        description="",
        instructions="do",
        **kwargs,
    )


def test_model_resolution_falls_back_to_default_model():
    builder = _builder(SimpleNamespace(agent_default_model="default"))
    spec = _spec()
    result = builder.build_agent(
        spec=spec,
        runtime_ctx=None,
        agents={},
        spec_map={"orchestrator": spec},
        validate_prompts=False,
    )
    assert str(result.agent.model) == "default"


def test_model_resolution_uses_spec_model_when_set():
    builder = _builder(SimpleNamespace(agent_default_model="default"))
    spec = _spec(model="spec-model")
    result = builder.build_agent(
        spec=spec,
        runtime_ctx=None,
        agents={},
        spec_map={"orchestrator": spec},
        validate_prompts=False,
    )
    assert str(result.agent.model) == "spec-model"


def test_model_resolution_uses_model_key_override_when_set():
    builder = _builder(SimpleNamespace(agent_default_model="default", agent_code_model="code-model"))
    spec = _spec(model_key="code")
    result = builder.build_agent(
        spec=spec,
        runtime_ctx=None,
        agents={},
        spec_map={"orchestrator": spec},
        validate_prompts=False,
    )
    assert str(result.agent.model) == "code-model"


def test_model_resolution_rejects_setting_both_model_and_model_key():
    builder = _builder(SimpleNamespace(agent_default_model="default", agent_code_model="code-model"))
    spec = _spec(model="spec-model", model_key="code")
    with pytest.raises(ValueError, match="must not set both 'model' and 'model_key'"):
        builder.build_agent(
            spec=spec,
            runtime_ctx=None,
            agents={},
            spec_map={"orchestrator": spec},
            validate_prompts=False,
        )


def test_model_resolution_rejects_empty_model_string():
    builder = _builder(SimpleNamespace(agent_default_model="default"))
    spec = _spec(model="")
    with pytest.raises(ValueError, match="invalid 'model' value"):
        builder.build_agent(
            spec=spec,
            runtime_ctx=None,
            agents={},
            spec_map={"orchestrator": spec},
            validate_prompts=False,
        )
