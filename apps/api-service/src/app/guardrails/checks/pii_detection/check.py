"""PII detection guardrail check implementation.

Uses regex patterns inspired by Microsoft Presidio for detecting
personally identifiable information.
"""

from __future__ import annotations

import base64
import re
import urllib.parse
from typing import Any

from app.guardrails._shared.specs import GuardrailCheckResult

# PII detection patterns (Presidio-inspired)
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL_ADDRESS": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        re.IGNORECASE,
    ),
    "PHONE_NUMBER": re.compile(
        r"(?:\+?1[-.\s]?)?"  # Country code
        r"(?:\(?\d{3}\)?[-.\s]?)"  # Area code
        r"\d{3}[-.\s]?\d{4}"  # Number
        r"(?:\s*(?:ext|x|extension)\s*\d+)?",  # Extension
        re.IGNORECASE,
    ),
    "US_SSN": re.compile(
        r"\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|"  # Visa
        r"5[1-5][0-9]{14}|"  # Mastercard
        r"3[47][0-9]{13}|"  # Amex
        r"6(?:011|5[0-9]{2})[0-9]{12}|"  # Discover
        r"(?:2131|1800|35\d{3})\d{11})\b"  # JCB
    ),
    "IP_ADDRESS": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    "US_PASSPORT": re.compile(
        r"\b[A-Z]?\d{8,9}\b"
    ),
    "US_DRIVER_LICENSE": re.compile(
        r"\b[A-Z]{1,2}\d{5,8}\b",
        re.IGNORECASE,
    ),
    "US_BANK_NUMBER": re.compile(
        r"\b\d{8,17}\b"  # Bank account numbers are typically 8-17 digits
    ),
    "IBAN_CODE": re.compile(
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b",
        re.IGNORECASE,
    ),
    "CVV": re.compile(
        r"\b(?:cvv|cvc|cid|cvn)[\s:]*\d{3,4}\b",
        re.IGNORECASE,
    ),
    "DATE_OF_BIRTH": re.compile(
        r"\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b|"
        r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b"
    ),
}

# Mask format for each entity type
MASK_FORMATS: dict[str, str] = {
    "EMAIL_ADDRESS": "<EMAIL_ADDRESS>",
    "PHONE_NUMBER": "<PHONE_NUMBER>",
    "US_SSN": "<US_SSN>",
    "CREDIT_CARD": "<CREDIT_CARD>",
    "IP_ADDRESS": "<IP_ADDRESS>",
    "US_PASSPORT": "<US_PASSPORT>",
    "US_DRIVER_LICENSE": "<US_DRIVER_LICENSE>",
    "US_BANK_NUMBER": "<US_BANK_NUMBER>",
    "IBAN_CODE": "<IBAN_CODE>",
    "CVV": "<CVV>",
    "DATE_OF_BIRTH": "<DATE_OF_BIRTH>",
}


def detect_pii(
    text: str,
    entities: list[str],
) -> dict[str, list[str]]:
    """Detect PII entities in text.

    Args:
        text: The text to scan.
        entities: List of entity types to detect.

    Returns:
        Dictionary mapping entity types to lists of detected values.
    """
    detected: dict[str, list[str]] = {}

    for entity_type in entities:
        pattern = PII_PATTERNS.get(entity_type)
        if pattern is None:
            continue

        matches = pattern.findall(text)
        if matches:
            detected[entity_type] = list(set(matches))

    return detected


def mask_pii(
    text: str,
    entities: list[str],
) -> tuple[str, dict[str, list[str]]]:
    """Mask PII entities in text.

    Args:
        text: The text to process.
        entities: List of entity types to mask.

    Returns:
        Tuple of (masked_text, detected_entities).
    """
    detected: dict[str, list[str]] = {}
    masked_text = text

    for entity_type in entities:
        pattern = PII_PATTERNS.get(entity_type)
        if pattern is None:
            continue

        matches = pattern.findall(masked_text)
        if matches:
            detected[entity_type] = list(set(matches))
            mask = MASK_FORMATS.get(entity_type, f"<{entity_type}>")
            masked_text = pattern.sub(mask, masked_text)

    return masked_text, detected


def decode_and_detect(
    text: str,
    entities: list[str],
) -> dict[str, list[str]]:
    """Detect PII in encoded strings (Base64, URL-encoded).

    Args:
        text: The text containing potentially encoded content.
        entities: List of entity types to detect.

    Returns:
        Dictionary of detected entities from decoded content.
    """
    detected: dict[str, list[str]] = {}

    # Try to find and decode Base64 strings
    base64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
    for match in base64_pattern.findall(text):
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            found = detect_pii(decoded, entities)
            for entity_type, values in found.items():
                if entity_type not in detected:
                    detected[entity_type] = []
                detected[entity_type].extend(values)
        except Exception:
            pass

    # Try URL-decoded detection
    try:
        url_decoded = urllib.parse.unquote(text)
        if url_decoded != text:
            found = detect_pii(url_decoded, entities)
            for entity_type, values in found.items():
                if entity_type not in detected:
                    detected[entity_type] = []
                detected[entity_type].extend(values)
    except Exception:
        pass

    # Deduplicate
    for entity_type in detected:
        detected[entity_type] = list(set(detected[entity_type]))

    return detected


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute PII detection check.

    Args:
        content: The text content to check.
        config: Validated configuration dictionary.
        conversation_history: Not used for PII detection.
        context: Runtime context (not used).

    Returns:
        GuardrailCheckResult indicating if PII was detected.
    """
    entities: list[str] = config.get("entities", [])
    block_mode: bool = config.get("block", False)
    detect_encoded: bool = config.get("detect_encoded_pii", False)

    # Default to common PII types if not specified
    if not entities:
        entities = ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"]

    # Detect or mask PII
    if block_mode:
        detected = detect_pii(content, entities)
        masked_content = None
    else:
        masked_content, detected = mask_pii(content, entities)

    # Also check encoded content if configured
    if detect_encoded:
        encoded_detected = decode_and_detect(content, entities)
        for entity_type, values in encoded_detected.items():
            if entity_type not in detected:
                detected[entity_type] = []
            detected[entity_type].extend(values)
            detected[entity_type] = list(set(detected[entity_type]))

    pii_found = any(len(values) > 0 for values in detected.values())

    # In block mode, trigger tripwire if PII found
    # In mask mode, don't trigger (content is sanitized)
    tripwire = pii_found and block_mode

    return GuardrailCheckResult(
        tripwire_triggered=tripwire,
        masked_content=masked_content if not block_mode else None,
        info={
            "guardrail_name": "PII Detection",
            "pii_detected": pii_found,
            "detected_entities": detected,
            "entity_types_checked": entities,
            "block_mode": block_mode,
            "checked_text": masked_content if masked_content else content[:100] + "...",
        },
    )
