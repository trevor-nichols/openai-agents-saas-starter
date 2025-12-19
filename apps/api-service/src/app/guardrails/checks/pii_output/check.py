"""PII detection guardrail check for output stage (reuses input logic)."""

from app.guardrails.checks.pii_detection.check import run_check

__all__ = ["run_check"]
