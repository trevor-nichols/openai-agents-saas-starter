"""Standard tool guardrail preset (balanced safety for tools)."""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailCheckConfig, GuardrailPreset


def get_preset() -> GuardrailPreset:
    """Return the standard tool guardrail preset."""
    return GuardrailPreset(
        key="tool_standard",
        display_name="Tool Standard Safety",
        description="Balanced safety for tool calls: PII masking + prompt injection detection.",
        guardrails=(
            # Tool input: PII masking (non-blocking by default)
            GuardrailCheckConfig(
                guardrail_key="pii_tool_input",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": False,
                },
                enabled=True,
            ),
            # Tool output: PII masking (non-blocking by default)
            GuardrailCheckConfig(
                guardrail_key="pii_tool_output",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": False,
                },
                enabled=True,
            ),
            # Tool input: prompt injection detection
            GuardrailCheckConfig(
                guardrail_key="prompt_injection_tool_input",
                config={
                    "model": "gpt-4.1-mini",
                    "confidence_threshold": 0.7,
                },
                enabled=True,
            ),
            # Tool output: prompt injection detection
            GuardrailCheckConfig(
                guardrail_key="prompt_injection_tool_output",
                config={
                    "model": "gpt-4.1-mini",
                    "confidence_threshold": 0.7,
                },
                enabled=True,
            ),
        ),
    )


__all__ = ["get_preset"]
