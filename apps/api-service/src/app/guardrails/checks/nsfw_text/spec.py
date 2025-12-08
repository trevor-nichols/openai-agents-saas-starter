"""NSFW text detection guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class NSFWTextConfig(BaseModel):
    """Configuration for NSFW text detection guardrail.

    Attributes:
        model: The LLM model to use for detection.
        confidence_threshold: Minimum confidence score (0.0-1.0) to trigger
            the tripwire.
    """

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for NSFW detection",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the NSFW text guardrail specification."""
    return GuardrailSpec(
        key="nsfw_text",
        display_name="NSFW Text",
        description=(
            "Detects not-safe-for-work or unprofessional content (profanity, "
            "explicit sexual content, graphic violence, harassment). Intended "
            "primarily for model outputs."
        ),
        stage="output",
        engine="llm",
        config_schema=NSFWTextConfig,
        check_fn_path="app.guardrails.checks.nsfw_text.check:run_check",
        uses_conversation_history=False,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
