"""Centralized imports for the OpenAI Agents SDK with a clear runtime error message."""

from __future__ import annotations

try:
    from agents import (
        Agent,
        ModelSettings,
        Runner,
        function_tool,
        set_default_openai_client,
        set_tracing_disabled,
    )
    from agents.items import MessageOutputItem, TResponseInputItem
    from agents.memory.session import SessionABC
except ImportError as exc:  # pragma: no cover - surfaced at runtime if missing
    raise SystemExit(
        "OpenAI Agents SDK is required. Install with `pip install openai openai-agents`."
    ) from exc

__all__ = [
    "Agent",
    "ModelSettings",
    "Runner",
    "function_tool",
    "set_default_openai_client",
    "set_tracing_disabled",
    "MessageOutputItem",
    "TResponseInputItem",
    "SessionABC",
]
