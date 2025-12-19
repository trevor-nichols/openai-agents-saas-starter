"""Standard guardrail preset for general use.

Provides balanced safety with reasonable latency. Suitable for most
production use cases.
"""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailCheckConfig, GuardrailPreset


def get_preset() -> GuardrailPreset:
    """Return the standard guardrail preset."""
    return GuardrailPreset(
        key="standard",
        display_name="Standard Safety",
        description=(
            "Balanced safety guardrails for general use. Includes moderation, "
            "jailbreak detection, and PII masking. Suitable for most production "
            "use cases with reasonable latency impact."
        ),
        guardrails=(
            # Pre-flight: PII masking (non-blocking, masks PII in input)
            GuardrailCheckConfig(
                guardrail_key="pii_detection_input",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": False,  # Mask, don't block
                },
                enabled=True,
            ),
            # Output: PII masking on responses (non-blocking by default)
            GuardrailCheckConfig(
                guardrail_key="pii_detection_output",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": False,
                },
                enabled=True,
            ),
            # Input: Content moderation
            GuardrailCheckConfig(
                guardrail_key="moderation",
                config={
                    "categories": ["hate", "violence", "self-harm", "sexual/minors"],
                    "threshold": 0.5,
                },
                enabled=True,
            ),
            # Input: Jailbreak detection
            GuardrailCheckConfig(
                guardrail_key="jailbreak_detection",
                config={
                    "model": "gpt-4.1-mini",
                    "confidence_threshold": 0.7,
                },
                enabled=True,
            ),
            # Output: URL filtering (allow all by default)
            GuardrailCheckConfig(
                guardrail_key="url_filter",
                config={
                    "url_allow_list": [],
                    "url_block_list": [],
                },
                enabled=False,  # Disabled by default in standard preset
            ),
        ),
    )
