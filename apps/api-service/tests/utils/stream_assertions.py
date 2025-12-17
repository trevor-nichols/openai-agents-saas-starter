from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlsplit, urlunsplit

from app.api.v1.shared.streaming import (
    AgentUpdatedEvent,
    ChunkDeltaEvent,
    ChunkDoneEvent,
    ContainerFileCitation,
    FileCitation,
    FileSearchResult,
    FunctionTool,
    FinalEvent,
    ErrorEvent,
    MessageCitationEvent,
    MessageDeltaEvent,
    McpTool,
    PublicSseEventBase,
    PublicSseEvent,
    ReasoningSummaryDeltaEvent,
    RefusalDeltaEvent,
    RefusalDoneEvent,
    ToolArgumentsDeltaEvent,
    ToolArgumentsDoneEvent,
    ToolApprovalEvent,
    ToolCodeDoneEvent,
    ToolOutputEvent,
    ToolStatusEvent,
    UrlCitation,
)


def _strip_query(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            key_lower = k.lower()
            if key_lower == "url" and isinstance(v, str):
                sanitized[k] = _strip_query(v)
            # Normalize vector store identifiers so goldens remain stable across re-recordings.
            # OpenAI assigns random IDs (e.g., vs_xxx) when creating stores; we rewrite them to a
            # deterministic placeholder that our contract tests assert against.
            elif key_lower == "vector_store_id" and isinstance(v, str):
                sanitized[k] = "vs_primary"
            else:
                sanitized[k] = _sanitize(v)
        return sanitized
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def record_stream(events: Sequence[PublicSseEventBase], path: Path) -> None:
    """Write sanitized streaming events to NDJSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            sanitized = _sanitize(json.loads(event.model_dump_json(by_alias=True)))
            f.write(json.dumps(sanitized, ensure_ascii=False))
            f.write("\n")


def maybe_record_stream(events: Sequence[PublicSseEventBase], *, env_var: str, default_path: Path) -> None:
    dest = os.getenv(env_var)
    if dest is None:
        return
    target = Path(dest or default_path)
    record_stream(events, target)


# ---------- Assertion helpers ----------


def assert_common_stream(events: Sequence[PublicSseEventBase]) -> None:
    assert events, "Expected at least one streaming event"

    terminal_indices = [
        idx for idx, event in enumerate(events) if isinstance(event, (FinalEvent, ErrorEvent))
    ]
    assert terminal_indices, "Stream must end with a terminal event (final/error)"
    assert len(terminal_indices) == 1, "Expected exactly one terminal event per stream"
    assert terminal_indices[0] == len(events) - 1, "Terminal event must be last in the stream"

    event_ids = [e.event_id for e in events]
    assert event_ids == sorted(event_ids), "event_id must be monotonically increasing"
    assert len(event_ids) == len(set(event_ids)), "event_id must be unique"

    schemas = {e.schema_ for e in events}
    assert schemas == {"public_sse_v1"}, f"Unexpected schema(s): {schemas}"

    stream_ids = {e.stream_id for e in events}
    assert len(stream_ids) == 1, "stream_id changed mid-stream"

    convo_ids = {e.conversation_id for e in events}
    assert len(convo_ids) == 1, "conversation_id changed mid-stream"

    provider_seqs = [e.provider_sequence_number for e in events if e.provider_sequence_number is not None]
    assert provider_seqs == sorted(provider_seqs), "provider_sequence_number should be monotonically increasing"


def assembled_text(events: Iterable[PublicSseEventBase]) -> str:
    return "".join(e.delta for e in events if isinstance(e, MessageDeltaEvent)).strip()


def collect_citations(events: Iterable[PublicSseEventBase]):
    citations = []
    for e in events:
        if isinstance(e, MessageCitationEvent):
            citations.append(e.citation)
    return citations


def _last_status_from_tool(events: Iterable[PublicSseEventBase], tool_type: str) -> str | None:
    statuses: list[str] = []
    for e in events:
        if not isinstance(e, ToolStatusEvent):
            continue
        if getattr(e.tool, "tool_type", None) != tool_type:
            continue
        status = getattr(e.tool, "status", None)
        if isinstance(status, str):
            statuses.append(status)
    return statuses[-1] if statuses else None


def assert_web_search_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "web_search")
    assert status == "completed", f"web_search_call did not complete (last={status})"

    citations = [c for c in collect_citations(events) if isinstance(c, UrlCitation)]
    assert citations, "Expected at least one url_citation annotation"
    assert all(a.url for a in citations), "Citation missing URL"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def assert_code_interpreter_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "code_interpreter")
    assert status == "completed", f"code_interpreter_call did not complete (last={status})"

    code_done = [e for e in events if isinstance(e, ToolCodeDoneEvent)]
    assert code_done, "Expected at least one tool.code.done event"
    assert any(e.code.strip() for e in code_done), "tool.code.done missing code"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"
    assert any(token in full_text for token in ["1.414", "1.41", "1.415", "1.4142"]), "Result not mentioned"


def assert_file_search_expectations(
    events: Sequence[PublicSseEventBase], *, expected_store_id: str | None = None
) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "file_search")
    assert status == "completed", f"file_search_call did not complete (last={status})"

    results: list[FileSearchResult] = []
    for e in events:
        if not isinstance(e, ToolStatusEvent):
            continue
        tool = e.tool
        if getattr(tool, "tool_type", None) != "file_search":
            continue
        tool_results = getattr(tool, "results", None)
        if isinstance(tool_results, list):
            for res in tool_results:
                if isinstance(res, FileSearchResult):
                    results.append(res)
                elif isinstance(res, dict):
                    results.append(FileSearchResult.model_validate(res))

    assert results, "Expected file_search results"
    if expected_store_id:
        assert any(r.vector_store_id == expected_store_id for r in results), (
            "Results did not reference the expected store"
        )

    citations = [
        c
        for c in collect_citations(events)
        if isinstance(c, (FileCitation, ContainerFileCitation))
    ]
    assert citations or results, "No file citations or results captured"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def assert_image_generation_expectations(
    events: Sequence[PublicSseEventBase], *, require_partial_chunks: bool = True
) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "image_generation")
    assert status in {"completed", "generating", "partial_image"}, (
        f"image_generation_call did not complete (last={status})"
    )

    terminal = events[-1]
    assert isinstance(terminal, FinalEvent), "Expected final terminal event for image generation golden"
    has_attachments = bool(terminal.final.attachments)
    assert has_attachments, "No attachments were stored from the image generation call"

    if require_partial_chunks:
        chunk_deltas = [
            e
            for e in events
            if isinstance(e, ChunkDeltaEvent) and e.target.field == "partial_image_b64"
        ]
        chunk_done = [
            e
            for e in events
            if isinstance(e, ChunkDoneEvent) and e.target.field == "partial_image_b64"
        ]
        assert chunk_deltas, "Expected chunk.delta events for partial_image_b64"
        assert chunk_done, "Expected chunk.done for partial_image_b64"


def assert_function_tool_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)

    statuses = [
        e
        for e in events
        if isinstance(e, ToolStatusEvent) and isinstance(e.tool, FunctionTool)
    ]
    assert statuses, "Expected tool.status events for a function tool call"
    assert any(e.tool.status == "in_progress" for e in statuses), "Function tool never started"
    assert any(e.tool.status == "completed" for e in statuses), "Function tool never completed"

    args_delta = [
        e for e in events if isinstance(e, ToolArgumentsDeltaEvent) and e.tool_type == "function"
    ]
    assert args_delta, "Expected tool.arguments.delta events for function tool args"

    args_done = [
        e for e in events if isinstance(e, ToolArgumentsDoneEvent) and e.tool_type == "function"
    ]
    assert args_done, "Expected tool.arguments.done for function tool args"
    assert args_done[-1].arguments_text, "tool.arguments.done missing arguments_text"

    outputs = [
        e for e in events if isinstance(e, ToolOutputEvent) and e.tool_type == "function"
    ]
    assert outputs, "Expected tool.output for function tool"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def assert_refusal_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)

    refusal_delta = [e for e in events if isinstance(e, RefusalDeltaEvent)]
    refusal_done = [e for e in events if isinstance(e, RefusalDoneEvent)]
    assert refusal_delta or refusal_done, "Expected refusal events"

    terminal = events[-1]
    assert isinstance(terminal, FinalEvent), "Refusal streams should end with final"
    assert terminal.final.status == "refused", f"Expected final.status=refused (got {terminal.final.status})"
    assert terminal.final.refusal_text, "Expected refusal_text in terminal payload"


def assert_provider_error_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)
    terminal = events[-1]
    assert isinstance(terminal, ErrorEvent), "Provider error golden should end with error"
    assert terminal.error.source == "provider"


def assert_reasoning_summary_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)

    deltas = [e for e in events if isinstance(e, ReasoningSummaryDeltaEvent)]
    assert deltas, "Expected reasoning_summary.delta events"
    summary_text = "".join(e.delta for e in deltas).strip()
    assert summary_text, "Reasoning summary deltas were empty"

    terminal = events[-1]
    assert isinstance(terminal, FinalEvent), "Reasoning summary streams should end with final"
    assert terminal.final.reasoning_summary_text, "Expected reasoning_summary_text in terminal payload"


def assert_mcp_tool_expectations(events: Sequence[PublicSseEventBase]) -> None:
    assert_common_stream(events)

    statuses = [
        e for e in events if isinstance(e, ToolStatusEvent) and isinstance(e.tool, McpTool)
    ]
    assert statuses, "Expected tool.status events for an MCP tool call"
    assert any(e.tool.status == "awaiting_approval" for e in statuses), "MCP approval not surfaced"
    assert any(e.tool.status == "completed" for e in statuses), "MCP tool never completed"

    approvals = [e for e in events if isinstance(e, ToolApprovalEvent)]
    assert approvals, "Expected tool.approval event for MCP tool call"

    args_done = [e for e in events if isinstance(e, ToolArgumentsDoneEvent) and e.tool_type == "mcp"]
    assert args_done, "Expected tool.arguments.done for MCP tool args"

    outputs = [e for e in events if isinstance(e, ToolOutputEvent) and e.tool_type == "mcp"]
    assert outputs, "Expected tool.output for MCP tool"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def assert_handoff_expectations(
    events: Sequence[PublicSseEventBase],
    *,
    expected_from: str | None = None,
    expected_to: str | None = None,
) -> None:
    assert_common_stream(events)

    updates = [e for e in events if isinstance(e, AgentUpdatedEvent)]
    assert updates, "Expected agent.updated event"
    if expected_from is not None:
        assert any(e.from_agent == expected_from for e in updates), "from_agent did not match"
    if expected_to is not None:
        assert any(e.to_agent == expected_to for e in updates), "to_agent did not match"

    terminal = events[-1]
    assert isinstance(terminal, FinalEvent), "Handoff streams should end with final"
    assert terminal.final.response_text or terminal.final.structured_output, "Expected final output"


def assert_workflow_expectations(
    events: Sequence[PublicSseEventBase],
    *,
    expected_workflow_key: str,
    expected_steps: set[str],
) -> None:
    assert_common_stream(events)

    assert all(e.workflow is not None for e in events), "Workflow events must include workflow context"
    assert all(
        e.workflow.workflow_key == expected_workflow_key
        for e in events
        if e.workflow is not None
    ), "workflow_key changed mid-stream"

    steps_seen = {
        e.workflow.step_name
        for e in events
        if e.workflow is not None and e.workflow.step_name
    }
    missing = expected_steps - steps_seen
    assert not missing, f"Missing workflow step(s): {sorted(missing)} (saw {sorted(steps_seen)})"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def load_stream_fixture(path: Path) -> list[PublicSseEventBase]:
    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return [PublicSseEvent.model_validate_json(line).root for line in lines]
