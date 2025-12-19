"""Custom prompt guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class CustomPromptConfig(BaseModel):
    """Configuration for custom prompt guardrail.

    Allows flexible, user-defined checks using natural language instructions.

    Attributes:
        model: The LLM model to use for the check.
        confidence_threshold: Minimum confidence score (0.0-1.0) to trigger
            the tripwire.
        system_prompt_details: Natural language description of what to check for.
            This is appended to a base system prompt.
    """

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for custom check",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )
    system_prompt_details: str = Field(
        default="Check if the content violates any policies.",
        description="Custom check instructions",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the custom prompt guardrail specification."""
    return GuardrailSpec(
        key="custom_prompt",
        display_name="Custom Prompt Check",
        description=(
            "A flexible, user-defined guardrail that uses natural language "
            "to specify what to check for. Useful for domain-specific rules "
            "not covered by built-in guardrails."
        ),
        stage="input",
        engine="llm",
        config_schema=CustomPromptConfig,
        check_fn_path="app.guardrails.checks.custom_prompt.check:run_check",
        uses_conversation_history=False,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
            "system_prompt_details": "Check if the content violates any policies.",
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
