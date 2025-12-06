"""RunConfig construction helpers for OpenAI agent runtime."""

from __future__ import annotations

from typing import Any

from agents.run import RunConfig

from app.agents._shared.handoff_filters import get_filter as get_handoff_filter
from app.domain.ai import RunOptions


def build_run_config(options: RunOptions | None) -> RunConfig | None:
    if not options:
        return None

    kwargs: dict[str, Any] = {}

    if options.handoff_input_filter:
        kwargs["handoff_input_filter"] = get_handoff_filter(options.handoff_input_filter)

    allowed = {
        "input_guardrails",
        "output_guardrails",
        "model",
        "model_settings",
        "tracing_disabled",
        "trace_include_sensitive_data",
        "workflow_name",
        "tool_resources",
    }
    if options.run_config:
        for key, value in options.run_config.items():
            if key in allowed:
                kwargs[key] = value

    if not kwargs:
        return None

    return RunConfig(**kwargs)


__all__ = ["build_run_config"]
