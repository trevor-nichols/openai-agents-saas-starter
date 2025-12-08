"""Hallucination detection guardrail for factual validation."""

from app.guardrails.checks.hallucination.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
