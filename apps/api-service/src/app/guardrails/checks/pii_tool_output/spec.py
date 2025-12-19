"""PII detection guardrail specification for tool output stage."""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailSpec
from app.guardrails.checks.pii_detection.spec import PIIDetectionConfig


def get_guardrail_spec() -> GuardrailSpec:
    """Return the PII detection guardrail specification for tool outputs."""
    return GuardrailSpec(
        key="pii_tool_output",
        display_name="PII Detection (Tool Output)",
        description=(
            "Detects PII in tool outputs. Can block or mask detected PII in tool responses."
        ),
        stage="tool_output",
        engine="regex",
        config_schema=PIIDetectionConfig,
        check_fn_path="app.guardrails.checks.pii_output.check:run_check",
        uses_conversation_history=False,
        default_config={
            "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
            "block": False,
            "detect_encoded_pii": False,
        },
        supports_masking=True,
        tripwire_on_error=False,
    )


__all__ = ["get_guardrail_spec"]
