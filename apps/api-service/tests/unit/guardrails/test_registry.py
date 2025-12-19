"""Tests for guardrail registry."""

from typing import Literal, Sequence

import pytest
from pydantic import BaseModel

from app.guardrails._shared.registry import GuardrailRegistry, get_guardrail_registry
from app.guardrails._shared.specs import (
    GuardrailCheckConfig,
    GuardrailPreset,
    GuardrailSpec,
)


class DummyConfig(BaseModel):
    """Dummy config schema for testing."""

    value: str = "default"


def make_test_spec(key: str, stage: Literal["pre_flight", "input", "output", "tool_input", "tool_output"] = "input") -> GuardrailSpec:
    """Create a test guardrail spec."""
    return GuardrailSpec(
        key=key,
        display_name=f"Test {key}",
        description=f"Test guardrail {key}",
        stage=stage,
        engine="regex",
        config_schema=DummyConfig,
        check_fn_path=f"app.guardrails.checks.{key}:run_check",
    )


def make_test_preset(key: str, guardrail_keys: Sequence[str]) -> GuardrailPreset:
    """Create a test guardrail preset."""
    return GuardrailPreset(
        key=key,
        display_name=f"Test {key}",
        description=f"Test preset {key}",
        guardrails=tuple(
            GuardrailCheckConfig(guardrail_key=gk) for gk in guardrail_keys
        ),
    )


class TestGuardrailRegistry:
    """Tests for GuardrailRegistry class."""

    def test_register_spec(self) -> None:
        registry = GuardrailRegistry()
        spec = make_test_spec("test_guard")

        registry.register_spec(spec)

        assert registry.get_spec("test_guard") == spec

    def test_register_duplicate_spec_raises(self) -> None:
        registry = GuardrailRegistry()
        spec = make_test_spec("duplicate")

        registry.register_spec(spec)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_spec(spec)

    def test_get_spec_not_found(self) -> None:
        registry = GuardrailRegistry()

        assert registry.get_spec("nonexistent") is None

    def test_list_specs(self) -> None:
        registry = GuardrailRegistry()
        spec1 = make_test_spec("guard1")
        spec2 = make_test_spec("guard2")

        registry.register_spec(spec1)
        registry.register_spec(spec2)

        specs = registry.list_specs()
        keys = [s.key for s in specs]
        assert "guard1" in keys
        assert "guard2" in keys

    def test_register_preset(self) -> None:
        registry = GuardrailRegistry()
        # Must register specs before preset that references them
        registry.register_spec(make_test_spec("guard1"))
        registry.register_spec(make_test_spec("guard2"))
        preset = make_test_preset("test_preset", ["guard1", "guard2"])

        registry.register_preset(preset)

        assert registry.get_preset("test_preset") == preset

    def test_register_duplicate_preset_raises(self) -> None:
        registry = GuardrailRegistry()
        preset = make_test_preset("duplicate", [])

        registry.register_preset(preset)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_preset(preset)

    def test_get_preset_not_found(self) -> None:
        registry = GuardrailRegistry()

        assert registry.get_preset("nonexistent") is None

    def test_list_presets(self) -> None:
        registry = GuardrailRegistry()
        preset1 = make_test_preset("preset1", [])
        preset2 = make_test_preset("preset2", [])

        registry.register_preset(preset1)
        registry.register_preset(preset2)

        presets = registry.list_presets()
        keys = [p.key for p in presets]
        assert "preset1" in keys
        assert "preset2" in keys


class TestGetGuardrailRegistry:
    """Tests for get_guardrail_registry singleton."""

    def test_returns_same_instance(self) -> None:
        registry1 = get_guardrail_registry()
        registry2 = get_guardrail_registry()

        assert registry1 is registry2

    def test_is_guardrail_registry(self) -> None:
        registry = get_guardrail_registry()

        assert isinstance(registry, GuardrailRegistry)
