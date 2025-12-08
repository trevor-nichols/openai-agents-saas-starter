"""PII detection guardrail specification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec

# Supported PII entity types
PIIEntityType = Literal[
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "US_PASSPORT",
    "US_DRIVER_LICENSE",
    "US_BANK_NUMBER",
    "IBAN_CODE",
    "CVV",
    "DATE_OF_BIRTH",
]


class PIIDetectionConfig(BaseModel):
    """Configuration for PII detection guardrail.

    Attributes:
        entities: List of PII entity types to detect. If empty, all
            supported entities are checked.
        block: If True, triggers tripwire when PII is found. If False,
            masks PII and allows content through.
        detect_encoded_pii: If True, also detects PII in Base64/URL-encoded
            strings.
    """

    entities: list[PIIEntityType] = Field(
        default=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
        description="PII entity types to detect",
    )
    block: bool = Field(
        default=False,
        description="Block content (True) or mask PII (False)",
    )
    detect_encoded_pii: bool = Field(
        default=False,
        description="Detect PII in encoded strings",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the PII detection guardrail specification for inputs/pre-flight."""
    return GuardrailSpec(
        key="pii_detection_input",
        display_name="PII Detection (Input)",
        description=(
            "Detects personally identifiable information (PII) such as SSNs, "
            "phone numbers, credit card numbers, and email addresses. Can mask "
            "detected PII or block content entirely."
        ),
        stage="pre_flight",
        engine="regex",
        config_schema=PIIDetectionConfig,
        check_fn_path="app.guardrails.checks.pii_detection.check:run_check",
        uses_conversation_history=False,
        default_config={
            "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"],
            "block": False,
            "detect_encoded_pii": False,
        },
        supports_masking=True,
        tripwire_on_error=False,
    )
