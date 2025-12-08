"""Minimal guardrail preset for low-latency applications.

Provides basic safety with minimal latency impact. Uses only
non-LLM based guardrails for fastest execution.
"""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailCheckConfig, GuardrailPreset


def get_preset() -> GuardrailPreset:
    """Return the minimal guardrail preset."""
    return GuardrailPreset(
        key="minimal",
        display_name="Minimal Latency",
        description=(
            "Lightweight guardrails with minimal latency impact. Uses only "
            "regex-based and API-based checks (no LLM calls). Suitable for "
            "latency-sensitive applications where speed is critical."
        ),
        guardrails=(
            # Pre-flight: PII masking only (regex-based, fast)
            GuardrailCheckConfig(
                guardrail_key="pii_detection_input",
                config={
                    "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
                    "block": False,
                    "detect_encoded_pii": False,  # Skip encoded detection for speed
                },
                enabled=True,
            ),
            # Input: Basic moderation (API-based, relatively fast)
            GuardrailCheckConfig(
                guardrail_key="moderation",
                config={
                    "categories": ["hate", "violence", "sexual/minors"],
                    "threshold": 0.7,  # Higher threshold for fewer flags
                },
                enabled=True,
            ),
            # Output: URL filtering (regex-based, fast)
            GuardrailCheckConfig(
                guardrail_key="url_filter",
                config={
                    "url_allow_list": [],
                    "url_block_list": [],
                },
                enabled=False,  # Disabled by default
            ),
        ),
    )
