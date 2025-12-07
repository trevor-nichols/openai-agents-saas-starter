"""Usage conversion helpers."""

from __future__ import annotations

from agents.usage import Usage

from app.domain.ai import AgentRunUsage


def convert_usage(usage: Usage | None) -> AgentRunUsage | None:
    if usage is None:
        return None

    # The SDK's Usage object may expose nested details; extract defensively to
    # avoid coupling to exact attribute shapes.
    def _get(obj, *path):
        cur = obj
        for key in path:
            cur = getattr(cur, key, None) if cur is not None else None
        return cur

    def _to_int(value) -> int | None:
        if isinstance(value, (int, float)):  # noqa: UP038 - tuple required for isinstance
            return int(value)
        return None

    def _normalize_requests(value: int | None) -> int:
        if value is None:
            return 1
        return max(0, value)

    return AgentRunUsage(
        input_tokens=_to_int(getattr(usage, "input_tokens", None)),
        output_tokens=_to_int(getattr(usage, "output_tokens", None)),
        total_tokens=_to_int(getattr(usage, "total_tokens", None)),
        cached_input_tokens=_to_int(_get(usage, "input_tokens_details", "cached_tokens")),
        reasoning_output_tokens=_to_int(
            _get(usage, "output_tokens_details", "reasoning_tokens")
        ),
        requests=_normalize_requests(_to_int(getattr(usage, "requests", None))),
        request_usage_entries=getattr(usage, "request_usage_entries", None),
    )


__all__ = ["convert_usage"]
