"""Prompt injection detection guardrail for tool call validation."""

from app.guardrails.checks.prompt_injection.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
