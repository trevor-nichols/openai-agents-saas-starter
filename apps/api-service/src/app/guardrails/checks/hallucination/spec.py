"""Hallucination detection guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class HallucinationConfig(BaseModel):
    """Configuration for hallucination detection guardrail.

    Attributes:
        model: The LLM model to use for validation.
        confidence_threshold: Minimum confidence score (0.0-1.0) to trigger
            the tripwire.
        knowledge_source: OpenAI vector store ID for reference documents.
            Must start with "vs_".
    """

    model: str = Field(
        default="gpt-4.1-mini",
        description="Model for hallucination detection",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to trigger tripwire",
    )
    knowledge_source: str | None = Field(
        default=None,
        description="Vector store ID for reference documents (vs_...)",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the hallucination detection guardrail specification."""
    return GuardrailSpec(
        key="hallucination",
        display_name="Hallucination Detection",
        description=(
            "Detects potential hallucinations by validating factual claims "
            "against reference documents. Uses OpenAI's file search to check "
            "claims against a knowledge base. Flags content that is contradicted "
            "or unsupported."
        ),
        stage="output",
        engine="llm",
        config_schema=HallucinationConfig,
        check_fn_path="app.guardrails.checks.hallucination.check:run_check",
        uses_conversation_history=False,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
            "knowledge_source": None,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
