"""Jailbreak detection guardrail for AI safety bypass attempts."""

from app.guardrails.checks.jailbreak_detection.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
