"""Prompt injection detection guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class PromptInjectionConfig(BaseModel):
    """Configuration for prompt injection detection guardrail.

    Attributes:
        model: The LLM model to use for detection analysis.
        confidence_threshold: Minimum confidence score (0.0-1.0) to trigger
            the tripwire.
    """

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for prompt injection detection",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the prompt injection detection guardrail specification."""
    return GuardrailSpec(
        key="prompt_injection",
        display_name="Prompt Injection Detection",
        description=(
            "Detects prompt injection attempts in tool calls and outputs. "
            "Validates that requested functions align with user intent and "
            "prevents data leakage through unrelated tool outputs."
        ),
        stage="output",
        engine="llm",
        config_schema=PromptInjectionConfig,
        check_fn_path="app.guardrails.checks.prompt_injection.check:run_check",
        uses_conversation_history=True,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
