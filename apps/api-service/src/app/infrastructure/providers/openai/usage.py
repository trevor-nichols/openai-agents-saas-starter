"""Usage conversion helpers."""

from __future__ import annotations

from agents.usage import Usage

from app.domain.ai import AgentRunUsage


def convert_usage(usage: Usage | None) -> AgentRunUsage | None:
    if usage is None:
        return None
    return AgentRunUsage(
        input_tokens=int(usage.input_tokens) if usage.input_tokens is not None else None,
        output_tokens=int(usage.output_tokens) if usage.output_tokens is not None else None,
    )


__all__ = ["convert_usage"]
