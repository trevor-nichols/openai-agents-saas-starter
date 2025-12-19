"""Tests for guardrail specification dataclasses."""

from typing import Literal, cast

import pytest
from pydantic import BaseModel

from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckConfig,
    GuardrailCheckResult,
    GuardrailPreset,
    GuardrailSpec,
    total_guardrail_token_usage,
)


class DummyConfig(BaseModel):
    """Dummy config schema for testing."""

    threshold: float = 0.5
    enabled: bool = True


STAGE_INPUT: Literal["input"] = "input"
ENGINE_REGEX: Literal["regex"] = "regex"


class TestGuardrailSpec:
    """Tests for GuardrailSpec dataclass."""

    def test_create_minimal_spec(self) -> None:
        spec = GuardrailSpec(
            key="test_guardrail",
            display_name="Test Guardrail",
            description="A test guardrail",
            stage=STAGE_INPUT,
            engine=ENGINE_REGEX,
            config_schema=DummyConfig,
            check_fn_path="app.guardrails.checks.test:run_check",
        )

        assert spec.key == "test_guardrail"
        assert spec.display_name == "Test Guardrail"
        assert spec.stage == "input"
        assert spec.engine == "regex"
        assert spec.uses_conversation_history is False
        assert spec.supports_masking is False
        assert spec.tripwire_on_error is False

    def test_spec_validate_config_success(self) -> None:
        spec = GuardrailSpec(
            key="test",
            display_name="Test",
            description="Test",
            stage=STAGE_INPUT,
            engine=ENGINE_REGEX,
            config_schema=DummyConfig,
            check_fn_path="app.test:check",
        )

        validated = cast(
            DummyConfig, spec.validate_config({"threshold": 0.8, "enabled": False})
        )
        assert validated.threshold == 0.8
        assert validated.enabled is False

    def test_spec_validate_config_uses_defaults(self) -> None:
        spec = GuardrailSpec(
            key="test",
            display_name="Test",
            description="Test",
            stage=STAGE_INPUT,
            engine=ENGINE_REGEX,
            config_schema=DummyConfig,
            check_fn_path="app.test:check",
        )

        validated = cast(DummyConfig, spec.validate_config({}))
        assert validated.threshold == 0.5
        assert validated.enabled is True

    def test_spec_validate_config_invalid_raises(self) -> None:
        spec = GuardrailSpec(
            key="test",
            display_name="Test",
            description="Test",
            stage=STAGE_INPUT,
            engine=ENGINE_REGEX,
            config_schema=DummyConfig,
            check_fn_path="app.test:check",
        )

        with pytest.raises(Exception):  # Pydantic ValidationError
            spec.validate_config({"threshold": "not_a_number"})


class TestGuardrailCheckResult:
    """Tests for GuardrailCheckResult dataclass."""

    def test_create_passed_result(self) -> None:
        result = GuardrailCheckResult(
            tripwire_triggered=False,
            info={"guardrail_name": "Test", "flagged": False},
        )

        assert result.tripwire_triggered is False
        assert result.info["flagged"] is False
        assert result.masked_content is None

    def test_create_flagged_result(self) -> None:
        result = GuardrailCheckResult(
            tripwire_triggered=True,
            info={
                "guardrail_name": "PII Detection",
                "flagged": True,
                "reason": "Found email address",
                "details": {"entities": ["email"]},
            },
        )

        assert result.tripwire_triggered is True
        assert result.info["flagged"] is True
        assert result.info["reason"] == "Found email address"
        assert result.info["details"] == {"entities": ["email"]}

    def test_create_masked_result(self) -> None:
        result = GuardrailCheckResult(
            tripwire_triggered=False,
            info={"guardrail_name": "PII Detection", "flagged": True},
            masked_content="Contact me at [EMAIL_REDACTED]",
        )

        assert result.info["flagged"] is True
        assert result.tripwire_triggered is False
        assert result.masked_content == "Contact me at [EMAIL_REDACTED]"

    def test_to_output_info(self) -> None:
        result = GuardrailCheckResult(
            tripwire_triggered=True,
            info={
                "guardrail_name": "Test",
                "flagged": True,
                "reason": "Test reason",
            },
            confidence=0.95,
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

        output = result.to_output_info()
        assert output["guardrail_name"] == "Test"
        assert output["flagged"] is True
        assert output["reason"] == "Test reason"
        assert output["token_usage"] == {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }

    def test_execution_failed_in_output_info(self) -> None:
        result = GuardrailCheckResult(
            tripwire_triggered=False,
            info={"guardrail_name": "Test", "flagged": False},
            execution_failed=True,
            original_exception=ValueError("boom"),
        )

        output = result.to_output_info()
        assert output["execution_failed"] is True
        assert "boom" in output["error"]


class TestGuardrailCheckConfig:
    """Tests for GuardrailCheckConfig dataclass."""

    def test_create_minimal_config(self) -> None:
        cfg = GuardrailCheckConfig(guardrail_key="pii_detection_input")

        assert cfg.guardrail_key == "pii_detection_input"
        assert cfg.enabled is True
        assert cfg.config == {}

    def test_create_with_overrides(self) -> None:
        cfg = GuardrailCheckConfig(
            guardrail_key="moderation",
            enabled=True,
            config={"threshold": 0.9},
        )

        assert cfg.guardrail_key == "moderation"
        assert cfg.config == {"threshold": 0.9}

    def test_disabled_config(self) -> None:
        cfg = GuardrailCheckConfig(
            guardrail_key="jailbreak_detection",
            enabled=False,
        )

        assert cfg.enabled is False


class TestGuardrailPreset:
    """Tests for GuardrailPreset dataclass."""

    def test_create_preset(self) -> None:
        preset = GuardrailPreset(
            key="standard",
            display_name="Standard Safety",
            description="Balanced safety preset",
            guardrails=(
                GuardrailCheckConfig(guardrail_key="moderation"),
                GuardrailCheckConfig(guardrail_key="pii_detection_input"),
            ),
        )

        assert preset.key == "standard"
        assert len(preset.guardrails) == 2
        assert preset.guardrails[0].guardrail_key == "moderation"

    def test_empty_preset(self) -> None:
        preset = GuardrailPreset(
            key="none",
            display_name="No Guardrails",
            description="Empty preset",
            guardrails=(),
        )

        assert len(preset.guardrails) == 0


class TestAgentGuardrailConfig:
    """Tests for AgentGuardrailConfig dataclass."""

    def test_preset_only(self) -> None:
        cfg = AgentGuardrailConfig(preset="standard")

        assert cfg.preset == "standard"
        assert cfg.guardrail_keys == ()
        assert cfg.guardrails == ()
        assert cfg.suppress_tripwire is False

    def test_explicit_keys_only(self) -> None:
        cfg = AgentGuardrailConfig(
            guardrail_keys=("pii_detection_input", "moderation"),
        )

        assert cfg.preset is None
        assert cfg.guardrail_keys == ("pii_detection_input", "moderation")

    def test_preset_with_overrides(self) -> None:
        cfg = AgentGuardrailConfig(
            preset="standard",
            guardrails=(
                GuardrailCheckConfig(
                    guardrail_key="pii_detection_input",
                    config={"block": True},
                ),
            ),
        )

        assert cfg.preset == "standard"
        assert len(cfg.guardrails) == 1
        assert cfg.guardrails[0].config == {"block": True}

    def test_suppress_tripwire(self) -> None:
        cfg = AgentGuardrailConfig(
            preset="strict",
            suppress_tripwire=True,
        )

        assert cfg.suppress_tripwire is True


class TestTokenUsageAggregation:
    """Tests for total_guardrail_token_usage helper."""

    def test_aggregates_values(self) -> None:
        r1 = GuardrailCheckResult(
            tripwire_triggered=False,
            info={},
            token_usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        )
        r2 = GuardrailCheckResult(
            tripwire_triggered=False,
            info={},
            token_usage={
                "prompt_tokens": 2,
                "completion_tokens": 3,
                "total_tokens": 5,
            },
        )

        totals = total_guardrail_token_usage([r1, r2])
        assert totals == {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20,
        }

    def test_handles_missing_usage(self) -> None:
        r1 = GuardrailCheckResult(
            tripwire_triggered=False,
            info={},
            token_usage=None,
        )
        totals = total_guardrail_token_usage([r1, None])
        assert totals == {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
