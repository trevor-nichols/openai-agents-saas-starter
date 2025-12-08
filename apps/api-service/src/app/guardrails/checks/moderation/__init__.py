"""OpenAI moderation guardrail for content policy enforcement."""

from app.guardrails.checks.moderation.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
