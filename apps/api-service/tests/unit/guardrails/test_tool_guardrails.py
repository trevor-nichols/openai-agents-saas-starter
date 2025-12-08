"""Tests for tool-level guardrails."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import Any, cast

import pytest
from agents.tool_guardrails import ToolGuardrailFunctionOutput, ToolInputGuardrailData
from app.core.settings import Settings
from pydantic import BaseModel

from app.guardrails._shared.builder import GuardrailBuilder
from app.guardrails._shared.registry import GuardrailRegistry
from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckResult,
    GuardrailCheckConfig,
    GuardrailPreset,
    GuardrailSpec,
    ToolGuardrailConfig,
)
from app.infrastructure.providers.openai.registry.tool_resolver import ToolResolver
from app.utils.tools import ToolRegistry


class DummyConfig(BaseModel):
    """Dummy config for tool guardrail tests."""

    tripwire: bool = False


async def dummy_tool_check(
    content: str,
    config: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Simple guardrail check that mirrors the tripwire flag."""
    return GuardrailCheckResult(
        tripwire_triggered=bool(config.get("tripwire")),
        info={"content": content, "context": context or {}},
    )


@pytest.fixture
def registry() -> GuardrailRegistry:
    reg = GuardrailRegistry()
    reg.register_spec(
        GuardrailSpec(
            key="test_tool_input",
            display_name="Test Tool Input",
            description="Test tool input guardrail",
            stage="tool_input",
            engine="regex",
            config_schema=DummyConfig,
            check_fn_path="tests.unit.guardrails.test_tool_guardrails:dummy_tool_check",
        )
    )
    reg.register_spec(
        GuardrailSpec(
            key="test_tool_output",
            display_name="Test Tool Output",
            description="Test tool output guardrail",
            stage="tool_output",
            engine="regex",
            config_schema=DummyConfig,
            check_fn_path="tests.unit.guardrails.test_tool_guardrails:dummy_tool_check",
        )
    )
    reg.register_preset(
        GuardrailPreset(
            key="tool_test_preset",
            display_name="Tool Test Preset",
            description="Preset with input and output guardrails",
            guardrails=(
                GuardrailCheckConfig(guardrail_key="test_tool_input"),
                GuardrailCheckConfig(guardrail_key="test_tool_output"),
            ),
        )
    )
    return reg


class TestToolGuardrailBuilder:
    def _dummy_data(self, *, content: str = "payload") -> SimpleNamespace:
        ctx = SimpleNamespace(tool_arguments=content, context=None, tool_name="t1")
        agent = SimpleNamespace(name="agent1")
        return SimpleNamespace(context=ctx, agent=agent, output=content)

    def _typed_input_data(self, *, content: str = "payload") -> ToolInputGuardrailData:
        return cast(ToolInputGuardrailData, self._dummy_data(content=content))

    def _typed_guardrail_fn(
        self, guard: Any
    ) -> Callable[[ToolInputGuardrailData], Awaitable[ToolGuardrailFunctionOutput]]:
        return cast(
            Callable[[ToolInputGuardrailData], Awaitable[ToolGuardrailFunctionOutput]],
            guard.guardrail_function,
        )

    @pytest.mark.asyncio
    async def test_build_tool_input_guardrails(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        cfg = AgentGuardrailConfig(guardrail_keys=("test_tool_input",))

        guards = builder.build_tool_input_guardrails(cfg)
        assert len(guards) == 1

        guardrail_fn = self._typed_guardrail_fn(guards[0])
        result = await guardrail_fn(self._typed_input_data())
        behavior_type = getattr(result.behavior, "type", None) or result.behavior.get("type")
        assert behavior_type == "allow"
        assert result.output_info["guardrail_name"] == "Test Tool Input"

    @pytest.mark.asyncio
    async def test_tool_guardrail_tripwire_respects_suppress(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        cfg_trip = AgentGuardrailConfig(
            guardrails=(
                GuardrailCheckConfig(
                    guardrail_key="test_tool_input",
                    config={"tripwire": True},
                ),
            )
        )

        guards = builder.build_tool_input_guardrails(cfg_trip)
        guardrail_fn = self._typed_guardrail_fn(guards[0])
        data = self._typed_input_data()

        result = await guardrail_fn(data)
        behavior_type = getattr(result.behavior, "type", None) or result.behavior.get("type")
        assert behavior_type == "raise_exception"

        suppress_cfg = AgentGuardrailConfig(
            guardrails=(
                GuardrailCheckConfig(
                    guardrail_key="test_tool_input",
                    config={"tripwire": True},
                ),
            ),
            suppress_tripwire=True,
        )
        guards_suppressed = builder.build_tool_input_guardrails(suppress_cfg)
        guardrail_fn_suppressed = self._typed_guardrail_fn(guards_suppressed[0])
        result_suppressed = await guardrail_fn_suppressed(data)
        behavior_type_suppressed = getattr(result_suppressed.behavior, "type", None) or result_suppressed.behavior.get("type")
        assert behavior_type_suppressed == "allow"

    @pytest.mark.asyncio
    async def test_tool_guardrail_handles_missing_agent(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        cfg = AgentGuardrailConfig(guardrail_keys=("test_tool_input",))

        guards = builder.build_tool_input_guardrails(cfg)

        # Deliberately omit agent attribute
        ctx = SimpleNamespace(tool_arguments="payload", context=None, tool_name="t1")
        data = SimpleNamespace(context=ctx, output="payload")

        guardrail_fn = self._typed_guardrail_fn(guards[0])
        result = await guardrail_fn(cast(ToolInputGuardrailData, data))
        behavior_type = getattr(result.behavior, "type", None) or result.behavior.get("type")
        assert behavior_type == "allow"
        assert result.output_info["guardrail_name"] == "Test Tool Input"

    def test_tool_resolver_attaches_guardrails(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        resolver = ToolResolver(
            tool_registry=ToolRegistry(),
            settings_factory=lambda: cast(Settings, SimpleNamespace()),  # not used by guardrail attachment
            guardrail_builder=builder,
        )

        tool_obj = SimpleNamespace()
        global_cfg = ToolGuardrailConfig(
            input=AgentGuardrailConfig(guardrail_keys=("test_tool_input",)),
            output=AgentGuardrailConfig(guardrail_keys=("test_tool_output",)),
        )

        resolver._attach_tool_guardrails(
            tool=tool_obj,
            tool_name="dummy",
            global_config=global_cfg,
            override_config=None,
        )

        assert hasattr(tool_obj, "tool_input_guardrails")
        assert hasattr(tool_obj, "tool_output_guardrails")
        assert len(tool_obj.tool_input_guardrails) == 1
        assert len(tool_obj.tool_output_guardrails) == 1

        # Override disable should remove guardrails
        tool_obj2 = SimpleNamespace()
        resolver._attach_tool_guardrails(
            tool=tool_obj2,
            tool_name="dummy",
            global_config=global_cfg,
            override_config=ToolGuardrailConfig(enabled=False),
        )
        assert not hasattr(tool_obj2, "tool_input_guardrails")
        assert not hasattr(tool_obj2, "tool_output_guardrails")

    def test_builder_handles_tool_preset_with_mixed_stages(self, registry: GuardrailRegistry) -> None:
        builder = GuardrailBuilder(registry)
        preset_cfg = AgentGuardrailConfig(preset="tool_test_preset")

        input_guards = builder.build_tool_input_guardrails(preset_cfg)
        output_guards = builder.build_tool_output_guardrails(preset_cfg)

        # preset contains both stages; each builder should pick the matching one only
        assert len(input_guards) == 1
        assert input_guards[0].name == "Test Tool Input"
        assert len(output_guards) == 1
        assert output_guards[0].name == "Test Tool Output"
