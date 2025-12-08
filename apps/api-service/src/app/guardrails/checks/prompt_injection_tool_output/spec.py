"""Prompt injection detection guardrail specification for tool output stage."""

from __future__ import annotations

from app.guardrails._shared.specs import GuardrailSpec
from app.guardrails.checks.prompt_injection.spec import PromptInjectionConfig


def get_guardrail_spec() -> GuardrailSpec:
    """Return the prompt injection guardrail spec for tool output."""
    return GuardrailSpec(
        key="prompt_injection_tool_output",
        display_name="Prompt Injection (Tool Output)",
        description="Detects prompt injection attempts in tool outputs after execution.",
        stage="tool_output",
        engine="llm",
        config_schema=PromptInjectionConfig,
        check_fn_path="app.guardrails.checks.prompt_injection.check:run_check",
        uses_conversation_history=True,
        default_config={
            "model": "gpt-4.1-mini",
            "confidence_threshold": 0.7,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )


__all__ = ["get_guardrail_spec"]
