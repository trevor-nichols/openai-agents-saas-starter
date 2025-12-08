"""Tests for guardrail loaders."""

import pytest

from app.guardrails._shared.loaders import (
    initialize_guardrails,
    load_guardrail_presets,
    load_guardrail_specs,
)
from app.guardrails._shared.registry import GuardrailRegistry, get_guardrail_registry


class TestLoadGuardrailSpecs:
    """Tests for load_guardrail_specs function."""

    def test_loads_all_built_in_specs(self) -> None:
        specs = load_guardrail_specs()

        # Verify we have all expected guardrails
        keys = [s.key for s in specs]
        assert "url_filter" in keys
        assert "moderation" in keys
        assert "pii_detection_input" in keys
        assert "pii_detection_output" in keys
        assert "jailbreak_detection" in keys
        assert "prompt_injection" in keys
        assert "hallucination" in keys
        assert "custom_prompt" in keys

    def test_specs_have_valid_structure(self) -> None:
        specs = load_guardrail_specs()

        for spec in specs:
            assert spec.key, "spec must have a key"
            assert spec.display_name, "spec must have display_name"
            assert spec.description, "spec must have description"
            assert spec.stage in (
                "pre_flight",
                "input",
                "output",
                "tool_input",
                "tool_output",
            )
            assert spec.engine in ("regex", "llm", "api", "hybrid")
            assert spec.check_fn_path, "spec must have check_fn_path"
            assert spec.config_schema is not None


class TestLoadGuardrailPresets:
    """Tests for load_guardrail_presets function."""

    def test_loads_all_built_in_presets(self) -> None:
        presets = load_guardrail_presets()

        keys = [p.key for p in presets]
        assert "standard" in keys
        assert "strict" in keys
        assert "minimal" in keys

    def test_presets_have_valid_structure(self) -> None:
        presets = load_guardrail_presets()

        for preset in presets:
            assert preset.key, "preset must have a key"
            assert preset.display_name, "preset must have display_name"
            assert preset.description, "preset must have description"
            # guardrails can be list or tuple depending on dataclass definition
            assert isinstance(preset.guardrails, (list, tuple))


class TestInitializeGuardrails:
    """Tests for initialize_guardrails function."""

    def test_populates_registry(self) -> None:
        # Get fresh registry (uses singleton but specs/presets accumulate)
        initialize_guardrails()
        registry = get_guardrail_registry()

        # Verify specs are registered
        assert len(registry.list_specs()) >= 7  # At least our 7 built-in checks

        # Verify presets are registered
        assert len(registry.list_presets()) >= 3  # At least our 3 built-in presets

    def test_idempotent_initialization(self) -> None:
        registry = get_guardrail_registry()
        initial_spec_count = len(registry.list_specs())
        initial_preset_count = len(registry.list_presets())

        # Initialize again should not duplicate
        initialize_guardrails()

        assert len(registry.list_specs()) == initial_spec_count
        assert len(registry.list_presets()) == initial_preset_count


class TestPresetContents:
    """Tests for preset contents validity."""

    def test_standard_preset_guardrails(self) -> None:
        initialize_guardrails()
        registry = get_guardrail_registry()
        preset = registry.get_preset("standard")

        assert preset is not None
        keys = [g.guardrail_key for g in preset.guardrails]
        assert "moderation" in keys
        assert "pii_detection_input" in keys
        assert "pii_detection_output" in keys
        assert "url_filter" in keys

    def test_strict_preset_has_more_guardrails(self) -> None:
        initialize_guardrails()
        registry = get_guardrail_registry()

        standard = registry.get_preset("standard")
        strict = registry.get_preset("strict")

        assert standard is not None
        assert strict is not None
        assert len(strict.guardrails) >= len(standard.guardrails)

    def test_minimal_preset_is_lightweight(self) -> None:
        initialize_guardrails()
        registry = get_guardrail_registry()

        minimal = registry.get_preset("minimal")
        standard = registry.get_preset("standard")

        assert minimal is not None
        assert standard is not None
        # Minimal should have fewer or equal guardrails
        assert len(minimal.guardrails) <= len(standard.guardrails)
