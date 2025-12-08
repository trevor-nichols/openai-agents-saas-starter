"""Provider-neutral value objects for AI agent orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
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
    last_seen_at: datetime | None = None
    memory_strategy_defaults: dict[str, Any] | None = None


@dataclass(slots=True)
class AgentRunUsage:
    """Minimal usage snapshot propagated to billing/analytics layers."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    requests: int | None = None
    # Optional per-request usage entries as returned by the Agents SDK
    request_usage_entries: list[Mapping[str, Any]] | None = None


@dataclass(slots=True)
class AgentRunResult:
    """Normalized payload returned by provider runtimes."""

    final_output: Any
    response_id: str | None = None
    usage: AgentRunUsage | None = None
    metadata: Mapping[str, Any] | None = None
    # When the provider returns structured (non-string) output, retain it separately.
    structured_output: Any | None = None
    # Best-effort string form for downstream consumers that expect text.
    response_text: str | None = None
    # Raw tool outputs (e.g., image_generation_call) when available.
    tool_outputs: list[Mapping[str, Any]] | None = None
    # Handoff metadata (best effort; may be None if provider doesn't expose).
    handoff_count: int | None = None
    final_agent: str | None = None


@dataclass(slots=True)
class RunOptions:
    """Provider-agnostic knobs forwarded into SDK runs."""

    max_turns: int | None = None
    previous_response_id: str | None = None
    # Raw RunConfig kwargs; providers decide which keys they support.
    run_config: Mapping[str, Any] | None = None
    # Global handoff input filter name (provider-resolved).
    handoff_input_filter: str | None = None
    # Hook sink used to surface lifecycle events (e.g., to SSE).
    hook_sink: Any | None = None


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

    kind: Literal[
        "raw_response_event",
        "run_item_stream_event",
        "agent_updated_stream_event",
        "guardrail_result",
        "usage",
        "error",
        "lifecycle",
    ]

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

    # Workflow metadata (optional)
    workflow_key: str | None = None
    workflow_run_id: str | None = None
    step_name: str | None = None
    step_agent: str | None = None
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None

    # Agent routing
    agent: str | None = None
    new_agent: str | None = None

    # Streaming content helpers
    text_delta: str | None = None
    reasoning_delta: str | None = None

    # Lifecycle event descriptor (for hooks)
    event: str | None = None

    # Terminal marker for the stream consumer
    is_terminal: bool = False

    # Arbitrary structured payload for consumers that need full fidelity
    payload: Mapping[str, Any] | None = None

    # Optional attachment references created while streaming (e.g., stored image ids)
    attachments: list[Mapping[str, Any]] | None = None

    # Optional metadata for parity with non-stream responses
    metadata: Mapping[str, Any] | None = None

    # Structured output / text equivalents for final outputs when present
    structured_output: Any | None = None
    response_text: str | None = None

    # Typed enrichments for downstream consumers
    raw_event: Mapping[str, Any] | None = None
    tool_call: Mapping[str, Any] | None = None
    annotations: list[Mapping[str, Any]] | None = None

    # Guardrail metadata (emitted when kind == "guardrail_result")
    guardrail_stage: str | None = None  # pre_flight|input|output|tool_input|tool_output
    guardrail_key: str | None = None
    guardrail_name: str | None = None
    guardrail_tripwire_triggered: bool | None = None
    guardrail_suppressed: bool | None = None
    guardrail_flagged: bool | None = None
    guardrail_confidence: float | None = None
    guardrail_masked_content: str | None = None
    guardrail_token_usage: Mapping[str, Any] | None = None
    guardrail_details: Mapping[str, Any] | None = None
    guardrail_summary: bool = False

    @staticmethod
    def _strip_unserializable(obj: Any) -> Any:
        """Remove or coerce values that JSON encoders can't handle (e.g., callables)."""

        # Primitive fast path
        if obj is None or isinstance(obj, str | int | float | bool):
            return obj

        # Pydantic models (e.g., OpenAI Responses payloads)
        model_dump = getattr(obj, "model_dump", None)
        if callable(model_dump):
            return AgentStreamEvent._strip_unserializable(
                model_dump(mode="json", exclude_none=True)
            )

        # Dataclasses / mappings / sequences
        if callable(obj):
            name = getattr(obj, "__name__", obj.__class__.__name__)
            return f"<callable {name}>"
        if isinstance(obj, Mapping):
            cleaned: dict[str, Any] = {}
            for key, value in obj.items():
                if callable(value):
                    continue
                cleaned[key] = AgentStreamEvent._strip_unserializable(value)
            return cleaned
        if isinstance(obj, list | tuple | set):
            return [AgentStreamEvent._strip_unserializable(v) for v in obj]

        # Conservative fallback: string representation to keep streaming resilient.
        return repr(obj)

    @staticmethod
    def _to_mapping(obj: Any) -> Mapping[str, Any] | None:
        """Best-effort conversion to a JSON-friendly mapping for SSE payloads."""

        if obj is None:
            return None
        if isinstance(obj, Mapping):
            return AgentStreamEvent._strip_unserializable(obj)
        if is_dataclass(obj) and not isinstance(obj, type):
            return AgentStreamEvent._strip_unserializable(asdict(obj))
        model_dump = getattr(obj, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, Mapping):
                return AgentStreamEvent._strip_unserializable(dumped)
            return {"value": dumped}
        dict_fn = getattr(obj, "dict", None)
        if callable(dict_fn):
            try:
                dumped = dict_fn()
            except TypeError:  # pragma: no cover - fallback when dict() needs params
                dumped = dict_fn(exclude_none=True)
            if isinstance(dumped, Mapping):
                return AgentStreamEvent._strip_unserializable(dict(dumped))
            return {"value": dumped}
        __dict__ = getattr(obj, "__dict__", None)
        if isinstance(__dict__, Mapping):
            return AgentStreamEvent._strip_unserializable(dict(__dict__))
        return {"repr": repr(obj)}


__all__ = [
    "AgentDescriptor",
    "AgentRunResult",
    "AgentRunUsage",
    "AgentStreamEvent",
    "RunOptions",
]
