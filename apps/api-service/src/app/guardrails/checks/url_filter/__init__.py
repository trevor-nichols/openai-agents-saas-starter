"""URL filter guardrail for allow/block list URL validation."""

from app.guardrails.checks.url_filter.spec import get_guardrail_spec

__all__ = ["get_guardrail_spec"]
