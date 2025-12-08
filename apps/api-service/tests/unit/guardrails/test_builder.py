"""Tests for guardrail builder."""

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from app.guardrails._shared.builder import GuardrailBuilder
from app.guardrails._shared.loaders import initialize_guardrails
from app.guardrails._shared.registry import GuardrailRegistry, get_guardrail_registry
from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckConfig,
    GuardrailCheckResult,
    GuardrailPreset,
    GuardrailSpec,
)


class DummyConfig(BaseModel):
    """Dummy config for testing."""

    threshold: float = 0.5


async def dummy_check_fn(
    content: str,
    config: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Dummy check function for testing."""
    return GuardrailCheckResult(
        tripwire_triggered=False,
        info={"guardrail_name": "Dummy", "flagged": False, "content": content},
    )


async def dummy_tool_check_fn(
    content: str,
    config: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Dummy tool check function for testing."""
    return GuardrailCheckResult(
        tripwire_triggered=False,
        info={"guardrail_name": "Dummy Tool", "flagged": False, "content": content},
    )


class TestGuardrailBuilder:
    """Tests for GuardrailBuilder class."""

    @pytest.fixture
    def registry(self) -> GuardrailRegistry:
        """Create a test registry with a dummy spec."""
        reg = GuardrailRegistry()
        spec = GuardrailSpec(
            key="test_input_guard",
            display_name="Test Input Guard",
            description="Test input guardrail",
            stage="input",
            engine="regex",
            config_schema=DummyConfig,
            check_fn_path="tests.unit.guardrails.test_builder:dummy_check_fn",
        )
        reg.register_spec(spec)

        output_spec = GuardrailSpec(
            key="test_output_guard",
            display_name="Test Output Guard",
            description="Test output guardrail",
            stage="output",
            engine="regex",
            config_schema=DummyConfig,
            check_fn_path="tests.unit.guardrails.test_builder:dummy_check_fn",
        )
        reg.register_spec(output_spec)

        tool_input_spec = GuardrailSpec(
            key="test_tool_input_guard",
            display_name="Test Tool Input Guard",
            description="Test tool input guardrail",
            stage="tool_input",
            engine="regex",
            config_schema=DummyConfig,
            check_fn_path="tests.unit.guardrails.test_builder:dummy_tool_check_fn",
        )
        reg.register_spec(tool_input_spec)

        preset = GuardrailPreset(
            key="test_preset",
            display_name="Test Preset",
            description="Test preset",
            guardrails=(
                GuardrailCheckConfig(guardrail_key="test_input_guard"),
                GuardrailCheckConfig(guardrail_key="test_output_guard"),
            ),
        )
        reg.register_preset(preset)

        return reg

    def test_build_input_guardrails_from_keys(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("test_input_guard",))

        guardrails = builder.build_input_guardrails(config)

        assert len(guardrails) == 1
        assert guardrails[0].name == "Test Input Guard"

    def test_build_output_guardrails_from_keys(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("test_output_guard",))

        guardrails = builder.build_output_guardrails(config)

        assert len(guardrails) == 1
        assert guardrails[0].name == "Test Output Guard"

    def test_build_guardrails_from_preset(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(preset="test_preset")

        input_guards = builder.build_input_guardrails(config)
        output_guards = builder.build_output_guardrails(config)

        assert len(input_guards) == 1
        assert len(output_guards) == 1

    def test_unknown_guardrail_raises(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("nonexistent",))

        with pytest.raises(ValueError, match="not found"):
            builder.build_input_guardrails(config)

    def test_unknown_preset_raises(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(preset="nonexistent")

        with pytest.raises(ValueError, match="not found"):
            builder.build_input_guardrails(config)

    def test_empty_config_returns_empty_lists(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig()

        input_guards = builder.build_input_guardrails(config)
        output_guards = builder.build_output_guardrails(config)

        assert input_guards == []
        assert output_guards == []

    def test_explicit_disable_removes_from_preset(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(
            preset="test_preset",
            guardrails=(
                GuardrailCheckConfig(
                    guardrail_key="test_input_guard",
                    enabled=False,
                ),
            ),
        )

        input_guards = builder.build_input_guardrails(config)

        # The input guard should be disabled
        assert len(input_guards) == 0

    @pytest.mark.asyncio
    async def test_tool_input_guardrail_receives_arguments(
        self, registry: GuardrailRegistry
    ) -> None:
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("test_tool_input_guard",))

        tool_guards = builder.build_tool_input_guardrails(config)

        assert len(tool_guards) == 1

        guardrail_fn = tool_guards[0].guardrail_function
        data = SimpleNamespace(
            tool_arguments={"foo": "bar"},
            tool_name="demo_tool",
            agent=SimpleNamespace(name="agent_demo"),
            context=None,
        )

        result = await guardrail_fn(data)

        assert result.output_info["content"] == "{'foo': 'bar'}"
        assert result.output_info["guardrail_name"] == "Test Tool Input Guard"


class TestBuilderWithRealGuardrails:
    """Tests using the real guardrail specs."""

    @pytest.fixture(autouse=True)
    def setup_guardrails(self) -> None:
        """Initialize real guardrails."""
        initialize_guardrails()

    def test_build_from_standard_preset(self) -> None:
        registry = get_guardrail_registry()
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(preset="standard")

        input_guards = builder.build_input_guardrails(config)
        output_guards = builder.build_output_guardrails(config)

        # Standard preset should have some guardrails
        assert len(input_guards) > 0 or len(output_guards) > 0

    def test_build_moderation_guardrail(self) -> None:
        registry = get_guardrail_registry()
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("moderation",))

        # Moderation is an input guardrail
        input_guards = builder.build_input_guardrails(config)

        assert len(input_guards) == 1
        assert input_guards[0].name == "Moderation"

    def test_build_pii_detection_guardrail(self) -> None:
        registry = get_guardrail_registry()
        builder = GuardrailBuilder(registry)
        config = AgentGuardrailConfig(guardrail_keys=("pii_detection_input",))

        # PII detection is an input guardrail
        input_guards = builder.build_input_guardrails(config)

        assert len(input_guards) == 1
        assert input_guards[0].name == "PII Detection (Input)"
