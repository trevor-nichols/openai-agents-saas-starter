"""Provider-neutral value objects for AI agent orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Literal


@dataclass(slots=True)
class AgentDescriptor:
    """Metadata describing an agent entry point exposed to the API layer."""

    key: str
    display_name: str
    description: str
    model: str
    capabilities: tuple[str, ...] = ()
    status: Literal["active", "inactive", "error"] = "active"


@dataclass(slots=True)
class AgentRunUsage:
    """Minimal usage snapshot propagated to billing/analytics layers."""

    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(slots=True)
class AgentRunResult:
    """Normalized payload returned by provider runtimes."""

    final_output: str
    response_id: str | None = None
    usage: AgentRunUsage | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(slots=True)
class AgentStreamEvent:
    """Normalized streaming envelope the service can forward to clients.

    `kind` maps directly to the Agents SDK stream event union:
      - raw_response   -> underlying Responses API event
      - run_item       -> semantic agent milestone (tool call/output, message, etc.)
      - agent_update   -> current agent changed (handoff)
      - usage          -> terminal usage snapshot (optional)
      - error          -> transport/SDK error surfaced during streaming

    Convenience fields (text_delta, reasoning_delta, tool_name, etc.) are filled
    when present so the UI can render without re-inspecting the raw payload.
    """

    kind: Literal["raw_response", "run_item", "agent_update", "usage", "error"]

    conversation_id: str | None = None
    response_id: str | None = None
    sequence_number: int | None = None

    # Raw Responses API event info
    raw_type: str | None = None

    # Run item info
    run_item_name: str | None = None
    run_item_type: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None

    # Agent routing
    agent: str | None = None
    new_agent: str | None = None

    # Streaming content helpers
    text_delta: str | None = None
    reasoning_delta: str | None = None

    # Terminal marker for the stream consumer
    is_terminal: bool = False

    # Arbitrary structured payload for consumers that need full fidelity
    payload: Mapping[str, Any] | None = None

    @staticmethod
    def _to_mapping(obj: Any) -> Mapping[str, Any] | None:
        """Best-effort conversion to a JSON-friendly mapping for SSE payloads."""

        if obj is None:
            return None
        if isinstance(obj, Mapping):
            return obj
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        model_dump = getattr(obj, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, Mapping):
                return dumped
            return {"value": dumped}
        dict_fn = getattr(obj, "dict", None)
        if callable(dict_fn):
            try:
                dumped = dict_fn()
            except TypeError:  # pragma: no cover - fallback when dict() needs params
                dumped = dict_fn(exclude_none=True)
            if isinstance(dumped, Mapping):
                return dict(dumped)
            return {"value": dumped}
        __dict__ = getattr(obj, "__dict__", None)
        if isinstance(__dict__, Mapping):
            return dict(__dict__)
        return {"repr": repr(obj)}


__all__ = [
    "AgentDescriptor",
    "AgentRunResult",
    "AgentRunUsage",
    "AgentStreamEvent",
]
