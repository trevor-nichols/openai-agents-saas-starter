"""PII detection guardrail for personally identifiable information."""

from app.guardrails.checks.pii_detection.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
