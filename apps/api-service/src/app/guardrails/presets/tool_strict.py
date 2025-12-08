"""Strict tool guardrail preset (blocking for tool calls)."""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailCheckConfig, GuardrailPreset


def get_preset() -> GuardrailPreset:
    """Return the strict tool guardrail preset."""
    return GuardrailPreset(
        key="tool_strict",
        display_name="Tool Strict Safety",
        description="Stricter tool guardrails: block PII and lower tolerance for prompt injection.",
        guardrails=(
            GuardrailCheckConfig(
                guardrail_key="pii_tool_input",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": True,
                },
                enabled=True,
            ),
            GuardrailCheckConfig(
                guardrail_key="pii_tool_output",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": True,
                },
                enabled=True,
            ),
            GuardrailCheckConfig(
                guardrail_key="prompt_injection_tool_input",
                config={
                    "model": "gpt-4.1-mini",
                    "confidence_threshold": 0.8,
                },
                enabled=True,
            ),
            GuardrailCheckConfig(
                guardrail_key="prompt_injection_tool_output",
                config={
                    "model": "gpt-4.1-mini",
                    "confidence_threshold": 0.8,
                },
                enabled=True,
            ),
        ),
    )


__all__ = ["get_preset"]
