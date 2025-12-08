"""Off-topic prompts guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class OffTopicPromptsConfig(BaseModel):
    """Configuration for off-topic prompt detection guardrail."""

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for off-topic detection",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )
    system_prompt_details: str = Field(
        default="Your scope: keep conversation on the defined business domain.",
        description="Business scope and acceptable topics for the assistant.",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the off-topic prompts guardrail specification."""
    return GuardrailSpec(
        key="off_topic_prompts",
        display_name="Off Topic Prompts",
        description=(
            "Ensures user prompts stay within the defined business scope using LLM analysis. "
            "Flags content that goes off-topic to prevent scope creep."
        ),
        stage="input",
        engine="llm",
        config_schema=OffTopicPromptsConfig,
        check_fn_path="app.guardrails.checks.off_topic_prompts.check:run_check",
        uses_conversation_history=True,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
            "system_prompt_details": (
                "Customer support for our e-commerce platform. Topics include order status, "
                "returns, shipping, and product questions."
            ),
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
