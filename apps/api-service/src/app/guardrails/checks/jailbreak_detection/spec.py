"""Jailbreak detection guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class JailbreakDetectionConfig(BaseModel):
    """Configuration for jailbreak detection guardrail.

    Attributes:
        model: The LLM model to use for detection analysis.
        confidence_threshold: Minimum confidence score (0.0-1.0) to trigger
            the tripwire. Higher values reduce false positives.
        max_context_turns: Maximum number of conversation turns to include
            for multi-turn detection.
    """

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for jailbreak detection",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )
    max_context_turns: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max conversation turns for multi-turn detection",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the jailbreak detection guardrail specification."""
    return GuardrailSpec(
        key="jailbreak_detection",
        display_name="Jailbreak Detection",
        description=(
            "Detects attempts to bypass AI safety measures using LLM-based "
            "analysis. Identifies prompt injection, role-play requests to act "
            "as unrestricted entities, social engineering, and instruction "
            "override attempts. Supports multi-turn escalation detection."
        ),
        stage="input",
        engine="llm",
        config_schema=JailbreakDetectionConfig,
        check_fn_path="app.guardrails.checks.jailbreak_detection.check:run_check",
        uses_conversation_history=True,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
            "max_context_turns": 10,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
