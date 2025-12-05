import pytest
from jinja2 import UndefinedError

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry import OpenAIAgentRegistry


def _noop_search(*args, **kwargs):
    return []


def test_prompt_rendering_errors_on_missing_variables():
    spec = AgentSpec(
        key="missing_var_agent",
        display_name="Missing Var Agent",
        description="Should fail when prompt variable is absent",
        instructions="Hello {{ missing_var }}",
        capabilities=(),
    )

    settings = Settings()
    registry = OpenAIAgentRegistry(
        settings_factory=lambda: settings,
        conversation_searcher=_noop_search,
        specs=[spec],
    )

    runtime_ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="conv_test",
        request_message="hi",
        settings=settings,
    )

    with pytest.raises(UndefinedError):
        registry.get_agent_handle(
            "missing_var_agent",
            runtime_ctx=runtime_ctx,
            validate_prompts=True,
        )


def test_agent_without_runtime_ctx_still_validates_prompt():
    spec = AgentSpec(
        key="missing_var_agent",
        display_name="Missing Var Agent",
        description="Should fail when prompt variable is absent",
        instructions="Hello {{ missing_var }}",
        capabilities=(),
    )

    settings = Settings()
    registry = OpenAIAgentRegistry(
        settings_factory=lambda: settings,
        conversation_searcher=_noop_search,
        specs=[spec],
    )

    with pytest.raises(UndefinedError):
        registry.get_agent_handle(
            "missing_var_agent",
            runtime_ctx=None,
            validate_prompts=True,
        )


def test_multiple_default_agents_raise():
    specs = [
        AgentSpec(
            key="a",
            display_name="A",
            description="first",
            default=True,
            capabilities=(),
        ),
        AgentSpec(
            key="b",
            display_name="B",
            description="second",
            default=True,
            capabilities=(),
        ),
    ]
    settings = Settings()
    with pytest.raises(ValueError):
        OpenAIAgentRegistry(
            settings_factory=lambda: settings,
            conversation_searcher=_noop_search,
            specs=specs,
        )
