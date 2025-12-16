from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, cast

from app.api.v1.shared.streaming import (
    PUBLIC_SSE_SCHEMA_VERSION,
    ChunkDeltaEvent,
    ChunkDoneEvent,
    ChunkTarget,
    CodeInterpreterTool,
    ContainerFileCitation,
    ErrorEvent,
    ErrorPayload,
    FileCitation,
    FileSearchResult,
    FileSearchTool,
    FinalEvent,
    FinalPayload,
    FunctionTool,
    ImageGenerationTool,
    LifecycleEvent,
    McpTool,
    MessageAttachment,
    MessageCitationEvent,
    MessageDeltaEvent,
    PublicCitation,
    PublicUsage,
    ReasoningSummaryDeltaEvent,
    RefusalDeltaEvent,
    RefusalDoneEvent,
    StreamNotice,
    ToolArgumentsDeltaEvent,
    ToolArgumentsDoneEvent,
    ToolCodeDeltaEvent,
    ToolCodeDoneEvent,
    ToolOutputEvent,
    ToolStatusEvent,
    UrlCitation,
    WebSearchTool,
    WorkflowContext,
)
from app.domain.ai.models import AgentRunUsage, AgentStreamEvent

LifecycleStatus = Literal[
    "queued",
    "in_progress",
    "completed",
    "failed",
    "incomplete",
    "cancelled",
]

ToolType = Literal[
    "web_search",
    "file_search",
    "code_interpreter",
    "image_generation",
    "function",
    "mcp",
]
ArgsToolType = Literal["function", "mcp"]
SearchStatus = Literal["in_progress", "searching", "completed"]
CodeInterpreterStatus = Literal["in_progress", "interpreting", "completed"]
ImageGenerationStatus = Literal["in_progress", "generating", "partial_image", "completed"]
FinalStatus = Literal["completed", "failed", "incomplete", "refused", "cancelled"]


def _as_search_status(value: str | None) -> SearchStatus:
    if value in {"in_progress", "searching", "completed"}:
        return cast(SearchStatus, value)
    return "in_progress"


def _as_code_interpreter_status(value: str | None) -> CodeInterpreterStatus:
    if value in {"in_progress", "interpreting", "completed"}:
        return cast(CodeInterpreterStatus, value)
    return "in_progress"


def _as_image_generation_status(value: str | None) -> ImageGenerationStatus:
    if value in {"in_progress", "generating", "partial_image", "completed"}:
        return cast(ImageGenerationStatus, value)
    return "in_progress"


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return None


def _safe_json_parse(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


_SENSITIVE_KEY_SUBSTRINGS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "authorization",
    "token",
    "secret",
    "password",
    "passphrase",
    "bearer",
    "client_secret",
    "access_token",
    "refresh_token",
    "id_token",
)


def _is_sensitive_key(key: str) -> bool:
    key_lower = key.lower()
    return any(part in key_lower for part in _SENSITIVE_KEY_SUBSTRINGS)


def _truncate_string(*, value: str, path: str, max_chars: int) -> tuple[str, StreamNotice | None]:
    if len(value) <= max_chars:
        return value, None
    return (
        value[:max_chars],
        StreamNotice(
            type="truncated",
            path=path,
            message="Large content was truncated for streaming stability.",
        ),
    )


def _sanitize_json(obj: Any, *, path: str, max_string_chars: int) -> tuple[Any, list[StreamNotice]]:
    notices: list[StreamNotice] = []
    if isinstance(obj, dict):
        sanitized: dict[str, Any] = {}
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            if _is_sensitive_key(key):
                sanitized[key] = "<redacted>"
                notices.append(
                    StreamNotice(
                        type="redacted",
                        path=child_path,
                        message="Some fields were redacted for safety.",
                    )
                )
                continue
            coerced, child_notices = _sanitize_json(
                value, path=child_path, max_string_chars=max_string_chars
            )
            sanitized[key] = coerced
            notices.extend(child_notices)
        return sanitized, notices

    if isinstance(obj, list):
        sanitized_list: list[Any] = []
        for idx, value in enumerate(obj):
            child_path = f"{path}[{idx}]"
            coerced, child_notices = _sanitize_json(
                value, path=child_path, max_string_chars=max_string_chars
            )
            sanitized_list.append(coerced)
            notices.extend(child_notices)
        return sanitized_list, notices

    if isinstance(obj, str):
        truncated, notice = _truncate_string(value=obj, path=path, max_chars=max_string_chars)
        if notice:
            notices.append(notice)
        return truncated, notices

    return obj, notices


def _coerce_file_search_results(
    results: Any,
    *,
    max_results: int = 10,
    max_text_chars: int = 2_000,
) -> tuple[list[FileSearchResult] | None, list[StreamNotice]]:
    if not isinstance(results, list):
        return None, []

    coerced: list[FileSearchResult] = []
    notices: list[StreamNotice] = []
    for idx, item in enumerate(results[:max_results]):
        if not isinstance(item, dict):
            continue
        try:
            result = FileSearchResult.model_validate(item)
        except Exception:
            continue
        if isinstance(result.text, str):
            truncated, notice = _truncate_string(
                value=result.text,
                path=f"tool.results[{idx}].text",
                max_chars=max_text_chars,
            )
            if notice:
                notices.append(notice)
                result = result.model_copy(update={"text": truncated})
        coerced.append(result)

    if len(results) > max_results:
        notices.append(
            StreamNotice(
                type="truncated",
                path="tool.results",
                message=f"Results list truncated to {max_results} items.",
            )
        )
    return (coerced or None), notices


def _extract_urls(obj: Any, *, limit: int = 50) -> list[str]:
    found: list[str] = []

    def _walk(value: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(value, dict):
            url = value.get("url")
            if isinstance(url, str) and url:
                found.append(url)
            for child in value.values():
                _walk(child)
            return
        if isinstance(value, list):
            for child in value:
                _walk(child)

    _walk(obj)
    return found


def _as_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _tool_name_from_run_item(raw_item: dict[str, Any] | None) -> str | None:
    if not raw_item:
        return None
    # Function tools: raw_item.name
    name = raw_item.get("name")
    if isinstance(name, str) and name:
        return name
    # Hosted tools: infer from raw_item.type
    raw_type = raw_item.get("type")
    if raw_type == "web_search_call":
        return "web_search"
    if raw_type == "file_search_call":
        return "file_search"
    if raw_type == "code_interpreter_call":
        return "code_interpreter"
    if raw_type == "image_generation_call":
        return "image_generation"
    return None


def _workflow_context_from_meta(meta: Mapping[str, Any] | None) -> WorkflowContext | None:
    if not meta:
        return None
    branch_index = meta.get("branch_index")
    return WorkflowContext(
        workflow_key=_coerce_str(meta.get("workflow_key")),
        workflow_run_id=_coerce_str(meta.get("workflow_run_id")),
        stage_name=_coerce_str(meta.get("stage_name")),
        step_name=_coerce_str(meta.get("step_name")),
        step_agent=_coerce_str(meta.get("step_agent")),
        parallel_group=_coerce_str(meta.get("parallel_group")),
        branch_index=branch_index if isinstance(branch_index, int) else None,
    )


def _usage_to_public(usage: AgentRunUsage | None) -> PublicUsage | None:
    if usage is None:
        return None
    return PublicUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        cached_input_tokens=usage.cached_input_tokens,
        reasoning_output_tokens=usage.reasoning_output_tokens,
        requests=usage.requests,
    )


@dataclass(slots=True)
class _ToolState:
    tool_type: ToolType
    tool_name: str | None = None
    query: str | None = None
    sources: list[str] | None = None
    server_label: str | None = None
    last_status: str | None = None
    arguments_text: str = ""
    file_search_queries: list[str] | None = None
    file_search_results: list[FileSearchResult] | None = None
    container_id: str | None = None
    container_mode: Literal["auto", "explicit"] | None = None
    image_revised_prompt: str | None = None
    image_format: str | None = None
    image_size: str | None = None
    image_quality: str | None = None
    image_background: str | None = None
    image_partial_image_index: int | None = None


@dataclass(slots=True)
class PublicStreamProjector:
    """Stateful projection from internal AgentStreamEvent -> public SSE events (v1)."""

    stream_id: str
    max_chunk_chars: int = 131_072  # ~128KiB base64/text chunks for chunk.delta events

    _event_id: int = 0
    _lifecycle_status: LifecycleStatus | None = None
    _reasoning_summary_text: str = ""
    _refusal_text: str = ""
    _tool_state: dict[str, _ToolState] = field(default_factory=dict)
    _last_web_search_tool_call_id: str | None = None
    _attachments: list[MessageAttachment] = field(default_factory=list)
    _seen_attachment_ids: set[str] = field(default_factory=set)
    _terminal_emitted: bool = False

    @staticmethod
    def new_stream_id(*, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def _merge_tool_call_into_state(
        self, tool_call: Mapping[str, Any]
    ) -> tuple[str, str, str | None, list[StreamNotice]] | None:
        tool_type = tool_call.get("tool_type")
        if tool_type == "web_search":
            call = _as_dict(tool_call.get("web_search_call")) or {}
            tool_call_id = _coerce_str(call.get("id"))
            if not tool_call_id:
                return None
            status = _coerce_str(call.get("status"))
            state = self._tool_state.setdefault(tool_call_id, _ToolState(tool_type="web_search"))
            if status:
                state.last_status = status
            action = _as_dict(call.get("action")) or {}
            query = _coerce_str(action.get("query"))
            if query:
                state.query = query
            self._last_web_search_tool_call_id = tool_call_id
            return tool_call_id, "web_search", status, []

        if tool_type == "file_search":
            call = _as_dict(tool_call.get("file_search_call")) or {}
            tool_call_id = _coerce_str(call.get("id"))
            if not tool_call_id:
                return None
            status = _coerce_str(call.get("status"))
            state = self._tool_state.setdefault(tool_call_id, _ToolState(tool_type="file_search"))
            if status:
                state.last_status = status
            queries = call.get("queries")
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                state.file_search_queries = [q for q in queries if q]
            results, notices = _coerce_file_search_results(call.get("results"))
            if results is not None:
                state.file_search_results = results
            return tool_call_id, "file_search", status, notices

        if tool_type == "code_interpreter":
            call = _as_dict(tool_call.get("code_interpreter_call")) or {}
            tool_call_id = _coerce_str(call.get("id"))
            if not tool_call_id:
                return None
            status = _coerce_str(call.get("status"))
            state = self._tool_state.setdefault(
                tool_call_id, _ToolState(tool_type="code_interpreter")
            )
            if status:
                state.last_status = status
            state.container_id = _coerce_str(call.get("container_id")) or state.container_id
            container_mode = _coerce_str(call.get("container_mode"))
            if container_mode in {"auto", "explicit"}:
                state.container_mode = cast(Literal["auto", "explicit"], container_mode)
            return tool_call_id, "code_interpreter", status, []

        if tool_type == "image_generation":
            call = _as_dict(tool_call.get("image_generation_call")) or {}
            tool_call_id = _coerce_str(call.get("id"))
            if not tool_call_id:
                return None
            status = _coerce_str(call.get("status"))
            state = self._tool_state.setdefault(
                tool_call_id, _ToolState(tool_type="image_generation")
            )
            if status:
                state.last_status = status
            state.image_revised_prompt = (
                _coerce_str(call.get("revised_prompt")) or state.image_revised_prompt
            )
            state.image_format = _coerce_str(call.get("format")) or state.image_format
            state.image_size = _coerce_str(call.get("size")) or state.image_size
            state.image_quality = _coerce_str(call.get("quality")) or state.image_quality
            state.image_background = _coerce_str(call.get("background")) or state.image_background
            partial_index = call.get("partial_image_index")
            if isinstance(partial_index, int):
                state.image_partial_image_index = partial_index
            return tool_call_id, "image_generation", status, []

        return None

    def project(
        self,
        event: AgentStreamEvent,
        *,
        conversation_id: str,
        response_id: str | None,
        agent: str | None,
        workflow_meta: Mapping[str, Any] | None,
        server_timestamp: str | None = None,
    ) -> list[Any]:
        if self._terminal_emitted:
            return []

        ts = server_timestamp or _now_iso()
        workflow = _workflow_context_from_meta(workflow_meta)

        def _next_id() -> int:
            self._event_id += 1
            return self._event_id

        def _base_kwargs(
            kind: str,
            provider_seq: int | None = None,
            notices: list[StreamNotice] | None = None,
        ):
            return {
                "schema": PUBLIC_SSE_SCHEMA_VERSION,
                "kind": kind,
                "event_id": _next_id(),
                "stream_id": self.stream_id,
                "server_timestamp": ts,
                "conversation_id": conversation_id,
                "response_id": response_id,
                "agent": agent,
                "workflow": workflow,
                "provider_sequence_number": provider_seq,
                "notices": notices,
            }

        out: list[Any] = []

        # ----- Attachments (stored server-side; safe to reference) -----
        if isinstance(event.attachments, list):
            for item in event.attachments:
                if not isinstance(item, dict):
                    continue
                try:
                    att = MessageAttachment.model_validate(item)
                except Exception:
                    continue
                if att.object_id in self._seen_attachment_ids:
                    continue
                self._seen_attachment_ids.add(att.object_id)
                self._attachments.append(att)

        # ----- Terminal provider/server errors -----
        if event.kind == "raw_response_event" and event.raw_type == "error":
            raw = _as_dict(event.raw_event) or {}
            code = _coerce_str(raw.get("code"))
            message = _coerce_str(raw.get("message")) or "Provider error"
            out.append(
                ErrorEvent(
                    **_base_kwargs(kind="error", provider_seq=event.sequence_number),
                    error=ErrorPayload(
                        code=code,
                        message=message,
                        source="provider",
                        is_retryable=False,
                    ),
                )
            )
            self._terminal_emitted = True
            return out

        if event.kind == "error":
            payload = _as_dict(event.payload) or {}
            message = (
                _coerce_str(payload.get("message"))
                or _coerce_str(payload.get("error"))
                or "Server error"
            )
            out.append(
                ErrorEvent(
                    **_base_kwargs(kind="error"),
                    error=ErrorPayload(
                        code=None,
                        message=message,
                        source="server",
                        is_retryable=False,
                    ),
                )
            )
            self._terminal_emitted = True
            return out

        tool_call_notices: list[StreamNotice] = []
        tool_call = _as_dict(event.tool_call)
        merged = self._merge_tool_call_into_state(tool_call) if tool_call else None
        if merged:
            _tool_call_id, _tool_type, _status, tool_call_notices = merged
            if event.kind == "raw_response_event" and event.raw_type == "response.output_item.done":
                state = self._tool_state.get(_tool_call_id)
                if state:
                    if _tool_type == "file_search":
                        file_search_status = _as_search_status(state.last_status)
                        out.append(
                            ToolStatusEvent(
                                **_base_kwargs(
                                    kind="tool.status",
                                    provider_seq=event.sequence_number,
                                    notices=tool_call_notices or None,
                                ),
                                tool=FileSearchTool(
                                    tool_type="file_search",
                                    tool_call_id=_tool_call_id,
                                    status=file_search_status,
                                    queries=state.file_search_queries,
                                    results=state.file_search_results,
                                ),
                            )
                        )
                    elif _tool_type == "code_interpreter":
                        code_interpreter_status = _as_code_interpreter_status(state.last_status)
                        out.append(
                            ToolStatusEvent(
                                **_base_kwargs(
                                    kind="tool.status",
                                    provider_seq=event.sequence_number,
                                ),
                                tool=CodeInterpreterTool(
                                    tool_type="code_interpreter",
                                    tool_call_id=_tool_call_id,
                                    status=code_interpreter_status,
                                    container_id=state.container_id,
                                    container_mode=state.container_mode,
                                ),
                            )
                        )
                    elif _tool_type == "image_generation":
                        image_generation_status = _as_image_generation_status(state.last_status)
                        out.append(
                            ToolStatusEvent(
                                **_base_kwargs(
                                    kind="tool.status",
                                    provider_seq=event.sequence_number,
                                ),
                                tool=ImageGenerationTool(
                                    tool_type="image_generation",
                                    tool_call_id=_tool_call_id,
                                    status=image_generation_status,
                                    revised_prompt=state.image_revised_prompt,
                                    format=state.image_format,
                                    size=state.image_size,
                                    quality=state.image_quality,
                                    background=state.image_background,
                                    partial_image_index=state.image_partial_image_index,
                                ),
                            )
                        )
                    elif _tool_type == "web_search":
                        web_search_status = _as_search_status(state.last_status or "completed")
                        out.append(
                            ToolStatusEvent(
                                **_base_kwargs(
                                    kind="tool.status",
                                    provider_seq=event.sequence_number,
                                ),
                                tool=WebSearchTool(
                                    tool_type="web_search",
                                    tool_call_id=_tool_call_id,
                                    status=web_search_status,
                                    query=state.query,
                                    sources=state.sources,
                                ),
                            )
                        )

        # ----- Lifecycle (Responses API) -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            if event.raw_type.startswith("response."):
                lifecycle_map: dict[str, LifecycleStatus] = {
                    "response.created": "in_progress",
                    "response.in_progress": "in_progress",
                    "response.queued": "queued",
                    "response.completed": "completed",
                    "response.failed": "failed",
                    "response.incomplete": "incomplete",
                }
                lifecycle: LifecycleStatus | None = lifecycle_map.get(event.raw_type)
                if lifecycle:
                    self._lifecycle_status = lifecycle
                    out.append(
                        LifecycleEvent(
                            **_base_kwargs(kind="lifecycle", provider_seq=event.sequence_number),
                            status=lifecycle,
                        )
                    )

        # ----- Service lifecycle (e.g., workflow cancellation) -----
        if event.kind == "lifecycle":
            meta = event.metadata if isinstance(event.metadata, Mapping) else {}
            run_state = _coerce_str(meta.get("state"))
            if run_state in {"cancelled", "canceled"}:
                self._lifecycle_status = "cancelled"
                out.append(
                    LifecycleEvent(
                        **_base_kwargs(kind="lifecycle"),
                        status="cancelled",
                        reason=_coerce_str(meta.get("reason")),
                    )
                )

        # ----- Capture tool metadata from output items -----
        if (
            event.kind == "raw_response_event"
            and event.raw_type in {"response.output_item.added", "response.output_item.done"}
        ):
            raw = _as_dict(event.raw_event) or {}
            output_item = _as_dict(raw.get("item"))
            if output_item:
                item_type = _coerce_str(output_item.get("type"))
                item_id = _coerce_str(output_item.get("id"))
                if item_id and item_type in {"function_call", "mcp_call", "custom_tool_call"}:
                    tool_name = _coerce_str(
                        output_item.get("name") or output_item.get("tool_name")
                    )
                    if item_type == "mcp_call":
                        state = self._tool_state.setdefault(
                            item_id, _ToolState(tool_type="mcp")
                        )
                        if tool_name:
                            state.tool_name = tool_name
                        server_label = _coerce_str(
                            output_item.get("server_label") or output_item.get("server")
                        )
                        if server_label:
                            state.server_label = server_label
                    else:
                        state = self._tool_state.setdefault(
                            item_id,
                            _ToolState(tool_type="function"),
                        )
                        if tool_name:
                            state.tool_name = tool_name

        # ----- Message deltas -----
        if (
            event.kind == "raw_response_event"
            and event.raw_type == "response.output_text.delta"
            and event.text_delta is not None
        ):
            raw = _as_dict(event.raw_event) or {}
            message_id = _coerce_str(raw.get("item_id")) or "msg_unknown"
            out.append(
                MessageDeltaEvent(
                    **_base_kwargs(kind="message.delta", provider_seq=event.sequence_number),
                    message_id=message_id,
                    delta=event.text_delta,
                )
            )

        # ----- Citations -----
        if (
            event.kind == "raw_response_event"
            and event.raw_type == "response.output_text.annotation.added"
        ):
            raw = _as_dict(event.raw_event) or {}
            message_id = _coerce_str(raw.get("item_id")) or "msg_unknown"
            for ann in event.annotations or []:
                # event.annotations is already filtered to citation types.
                citation_type = ann.get("type")
                if citation_type == "url_citation":
                    citation: PublicCitation = UrlCitation.model_validate(ann)
                    if isinstance(citation, UrlCitation) and self._last_web_search_tool_call_id:
                        state = self._tool_state.setdefault(
                            self._last_web_search_tool_call_id,
                            _ToolState(tool_type="web_search"),
                        )
                        sources = state.sources or []
                        if citation.url not in sources:
                            state.sources = [*sources, citation.url]
                            # Citations can arrive after the tool status is already marked
                            # completed. Emit an updated tool.status so the UI can display the
                            # gathered sources without waiting for another provider status tick.
                            out.append(
                                ToolStatusEvent(
                                    **_base_kwargs(
                                        kind="tool.status",
                                        provider_seq=event.sequence_number,
                                    ),
                                    tool=WebSearchTool(
                                        tool_type="web_search",
                                        tool_call_id=self._last_web_search_tool_call_id,
                                        status=_as_search_status(state.last_status or "completed"),
                                        query=state.query,
                                        sources=state.sources,
                                    ),
                                )
                            )
                elif citation_type == "container_file_citation":
                    citation = ContainerFileCitation.model_validate(ann)
                else:
                    citation = FileCitation.model_validate(ann)
                out.append(
                    MessageCitationEvent(
                        **_base_kwargs(kind="message.citation", provider_seq=event.sequence_number),
                        message_id=message_id,
                        citation=citation,
                    )
                )

        # ----- Reasoning summary (summary-only) -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            if event.raw_type == "response.reasoning_summary_text.delta":
                delta = event.reasoning_delta or ""
                if delta:
                    self._reasoning_summary_text += delta
                    out.append(
                        ReasoningSummaryDeltaEvent(
                            **_base_kwargs(
                                kind="reasoning_summary.delta",
                                provider_seq=event.sequence_number,
                            ),
                            delta=delta,
                        )
                    )
            elif event.raw_type == "response.reasoning_summary_text.done":
                raw = _as_dict(event.raw_event) or {}
                text = raw.get("text")
                if isinstance(text, str) and text:
                    if not self._reasoning_summary_text:
                        self._reasoning_summary_text = text
                        out.append(
                            ReasoningSummaryDeltaEvent(
                                **_base_kwargs(
                                    kind="reasoning_summary.delta",
                                    provider_seq=event.sequence_number,
                                ),
                                delta=text,
                            )
                        )
                    elif text.startswith(self._reasoning_summary_text):
                        suffix = text[len(self._reasoning_summary_text) :]
                        if suffix:
                            self._reasoning_summary_text = text
                            out.append(
                                ReasoningSummaryDeltaEvent(
                                    **_base_kwargs(
                                        kind="reasoning_summary.delta",
                                        provider_seq=event.sequence_number,
                                    ),
                                    delta=suffix,
                                )
                            )

        # ----- Refusal -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            raw = _as_dict(event.raw_event) or {}
            if event.raw_type == "response.refusal.delta":
                refusal_delta = raw.get("delta")
                message_id = _coerce_str(raw.get("item_id")) or "msg_unknown"
                if isinstance(refusal_delta, str) and refusal_delta:
                    self._refusal_text += refusal_delta
                    out.append(
                        RefusalDeltaEvent(
                            **_base_kwargs(
                                kind="refusal.delta",
                                provider_seq=event.sequence_number,
                            ),
                            message_id=message_id,
                            delta=refusal_delta,
                        )
                    )
            elif event.raw_type == "response.refusal.done":
                refusal_text = raw.get("refusal")
                message_id = _coerce_str(raw.get("item_id")) or "msg_unknown"
                if isinstance(refusal_text, str) and refusal_text:
                    self._refusal_text = refusal_text
                    out.append(
                        RefusalDoneEvent(
                            **_base_kwargs(kind="refusal.done", provider_seq=event.sequence_number),
                            message_id=message_id,
                            refusal_text=refusal_text,
                        )
                    )

        # ----- Tool status from raw Responses events -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            raw = _as_dict(event.raw_event) or {}
            item_id = _coerce_str(raw.get("item_id"))
            if item_id:
                if event.raw_type.startswith("response.web_search_call."):
                    status_fragment = event.raw_type.rsplit(".", 1)[-1]
                    web_search_status = _as_search_status(status_fragment)
                    state = self._tool_state.setdefault(item_id, _ToolState(tool_type="web_search"))
                    state.tool_type = "web_search"
                    state.last_status = web_search_status
                    self._last_web_search_tool_call_id = item_id
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status", provider_seq=event.sequence_number),
                            tool=WebSearchTool(
                                tool_type="web_search",
                                tool_call_id=item_id,
                                status=web_search_status,
                                query=state.query,
                                sources=state.sources,
                            ),
                        )
                    )
                elif event.raw_type.startswith("response.file_search_call."):
                    status_fragment = event.raw_type.rsplit(".", 1)[-1]
                    file_search_status = _as_search_status(status_fragment)
                    state = self._tool_state.setdefault(
                        item_id, _ToolState(tool_type="file_search")
                    )
                    state.tool_type = "file_search"
                    state.last_status = file_search_status
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status", provider_seq=event.sequence_number),
                            tool=FileSearchTool(
                                tool_type="file_search",
                                tool_call_id=item_id,
                                status=file_search_status,
                                queries=state.file_search_queries,
                                results=state.file_search_results,
                            ),
                        )
                    )
                elif event.raw_type.startswith("response.code_interpreter_call."):
                    status_fragment = event.raw_type.rsplit(".", 1)[-1]
                    code_interpreter_status = _as_code_interpreter_status(status_fragment)
                    state = self._tool_state.setdefault(
                        item_id, _ToolState(tool_type="code_interpreter")
                    )
                    state.tool_type = "code_interpreter"
                    state.last_status = code_interpreter_status
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status", provider_seq=event.sequence_number),
                            tool=CodeInterpreterTool(
                                tool_type="code_interpreter",
                                tool_call_id=item_id,
                                status=code_interpreter_status,
                                container_id=state.container_id,
                                container_mode=state.container_mode,
                            ),
                        )
                    )
                elif event.raw_type.startswith("response.image_generation_call."):
                    status_fragment = event.raw_type.rsplit(".", 1)[-1]
                    image_generation_status = _as_image_generation_status(status_fragment)
                    state = self._tool_state.setdefault(
                        item_id, _ToolState(tool_type="image_generation")
                    )
                    state.tool_type = "image_generation"
                    state.last_status = image_generation_status
                    partial_image_index = raw.get("partial_image_index")
                    if not isinstance(partial_image_index, int):
                        partial_image_index = None
                    state.image_partial_image_index = partial_image_index
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status", provider_seq=event.sequence_number),
                            tool=ImageGenerationTool(
                                tool_type="image_generation",
                                tool_call_id=item_id,
                                status=image_generation_status,
                                revised_prompt=state.image_revised_prompt
                                or _coerce_str(raw.get("revised_prompt")),
                                format=state.image_format
                                or _coerce_str(raw.get("format") or raw.get("output_format")),
                                size=state.image_size or _coerce_str(raw.get("size")),
                                quality=state.image_quality or _coerce_str(raw.get("quality")),
                                background=state.image_background
                                or _coerce_str(raw.get("background")),
                                partial_image_index=partial_image_index,
                            ),
                        )
                    )

                    partial_b64 = raw.get("partial_image_b64") or raw.get("b64_json")
                    if (
                        image_generation_status == "partial_image"
                        and isinstance(partial_b64, str)
                        and partial_b64
                    ):
                        out.extend(
                            self._chunk_base64(
                                target=ChunkTarget(
                                    entity_kind="tool_call",
                                    entity_id=item_id,
                                    field="partial_image_b64",
                                    part_index=partial_image_index,
                                ),
                                next_base_kwargs=lambda kind: _base_kwargs(
                                    kind=kind,
                                    provider_seq=event.sequence_number,
                                ),
                                b64=partial_b64,
                            )
                        )
                elif event.raw_type.startswith("response.mcp_call."):
                    status_fragment = event.raw_type.rsplit(".", 1)[-1]
                    mcp_status: Literal["in_progress", "completed", "failed"] = "in_progress"
                    if status_fragment in {"in_progress", "completed", "failed"}:
                        mcp_status = cast(
                            Literal["in_progress", "completed", "failed"],
                            status_fragment,
                        )
                    state = self._tool_state.setdefault(item_id, _ToolState(tool_type="mcp"))
                    state.last_status = mcp_status
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status", provider_seq=event.sequence_number),
                            tool=McpTool(
                                tool_type="mcp",
                                tool_call_id=item_id,
                                status=mcp_status,
                                tool_name=state.tool_name or "unknown",
                                server_label=state.server_label,
                            ),
                        )
                    )

        # ----- Code interpreter code deltas/done -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            raw = _as_dict(event.raw_event) or {}
            item_id = _coerce_str(raw.get("item_id"))
            if item_id and event.raw_type == "response.code_interpreter_call_code.delta":
                code_delta = raw.get("delta")
                if isinstance(code_delta, str) and code_delta:
                    out.append(
                        ToolCodeDeltaEvent(
                            **_base_kwargs(
                                kind="tool.code.delta",
                                provider_seq=event.sequence_number,
                            ),
                            tool_call_id=item_id,
                            delta=code_delta,
                        )
                    )
            if item_id and event.raw_type == "response.code_interpreter_call_code.done":
                code = raw.get("code")
                if isinstance(code, str):
                    out.append(
                        ToolCodeDoneEvent(
                            **_base_kwargs(
                                kind="tool.code.done",
                                provider_seq=event.sequence_number,
                            ),
                            tool_call_id=item_id,
                            code=code,
                        )
                    )

        # ----- Function tool + MCP arguments -----
        if event.kind == "raw_response_event" and isinstance(event.raw_type, str):
            raw = _as_dict(event.raw_event) or {}
            item_id = _coerce_str(raw.get("item_id"))
            if item_id and event.raw_type in {
                "response.function_call_arguments.delta",
                "response.custom_tool_call_input.delta",
                "response.mcp_call_arguments.delta",
            }:
                arguments_delta = raw.get("delta")
                if isinstance(arguments_delta, str) and arguments_delta:
                    args_delta_tool_type: ArgsToolType = "function"
                    if "mcp_" in event.raw_type:
                        args_delta_tool_type = "mcp"
                    state = self._tool_state.setdefault(
                        item_id, _ToolState(tool_type=args_delta_tool_type)
                    )
                    state.arguments_text += arguments_delta

            if item_id and event.raw_type in {
                "response.function_call_arguments.done",
                "response.custom_tool_call_input.done",
                "response.mcp_call_arguments.done",
            }:
                args_done_tool_type: ArgsToolType = "function"
                if "mcp_" in event.raw_type:
                    args_done_tool_type = "mcp"
                state = self._tool_state.setdefault(
                    item_id, _ToolState(tool_type=args_done_tool_type)
                )
                if event.raw_type == "response.custom_tool_call_input.done":
                    arguments_text = raw.get("input")
                    tool_name = state.tool_name or "unknown"
                else:
                    arguments_text = raw.get("arguments")
                    tool_name = _coerce_str(raw.get("name")) or state.tool_name or "unknown"
                if isinstance(arguments_text, str):
                    parsed_json = _safe_json_parse(arguments_text)
                    notices: list[StreamNotice] = []

                    sanitized_json: dict[str, Any] | None = None
                    sanitized_text = arguments_text
                    if parsed_json is not None:
                        sanitized_any, notices = _sanitize_json(
                            parsed_json,
                            path="arguments_json",
                            max_string_chars=4_000,
                        )
                        sanitized_json = sanitized_any if isinstance(sanitized_any, dict) else None
                        if sanitized_json is not None:
                            sanitized_text = json.dumps(sanitized_json, ensure_ascii=False)

                    sanitized_text, truncated_notice = _truncate_string(
                        value=sanitized_text,
                        path="arguments_text",
                        max_chars=8_000,
                    )
                    if truncated_notice:
                        notices.append(truncated_notice)

                    state.arguments_text = sanitized_text
                    state.tool_name = tool_name
                    previously_emitted_status = state.last_status is not None
                    state.last_status = state.last_status or "in_progress"

                    if (
                        args_done_tool_type == "function"
                        and not previously_emitted_status
                        and state.last_status == "in_progress"
                    ):
                        out.append(
                            ToolStatusEvent(
                                **_base_kwargs(
                                    kind="tool.status",
                                    provider_seq=event.sequence_number,
                                ),
                                tool=FunctionTool(
                                    tool_type="function",
                                    tool_call_id=item_id,
                                    status="in_progress",
                                    name=tool_name,
                                ),
                            )
                        )
                    if sanitized_text:
                        chunk_size = 2_000
                        idx = 0
                        while idx < len(sanitized_text):
                            out.append(
                                ToolArgumentsDeltaEvent(
                                    **_base_kwargs(
                                        kind="tool.arguments.delta",
                                        provider_seq=event.sequence_number,
                                    ),
                                    tool_call_id=item_id,
                                    tool_type=args_done_tool_type,
                                    tool_name=tool_name,
                                    delta=sanitized_text[idx : idx + chunk_size],
                                )
                            )
                            idx += chunk_size
                    out.append(
                        ToolArgumentsDoneEvent(
                            **_base_kwargs(
                                kind="tool.arguments.done",
                                provider_seq=event.sequence_number,
                                notices=notices or None,
                            ),
                            tool_call_id=item_id,
                            tool_type=args_done_tool_type,
                            tool_name=tool_name,
                            arguments_text=sanitized_text,
                            arguments_json=sanitized_json,
                        )
                    )

        # ----- Run item tool lifecycle -----
        if event.kind == "run_item_stream_event" and event.run_item_name in {
            "tool_called",
            "tool_output",
            "mcp_approval_requested",
        }:
            payload = _as_dict(event.payload) or {}
            raw_item = _as_dict(payload.get("raw_item")) or payload
            raw_item_type = _coerce_str((raw_item or {}).get("type")) or event.run_item_type
            tool_call_id = (
                _coerce_str((raw_item or {}).get("call_id"))
                or _coerce_str((raw_item or {}).get("id"))
                or event.tool_call_id
            )
            if not tool_call_id:
                return out

            inferred = _tool_name_from_run_item(raw_item)
            raw_item_name = _coerce_str((raw_item or {}).get("name"))
            tool_name = inferred or event.tool_name or raw_item_name or "unknown"

            tool_type: ToolType = "function"
            if event.run_item_name == "mcp_approval_requested" or raw_item_type == "mcp_call":
                tool_type = "mcp"
            else:
                builtin_tool: str | None = None
                if raw_item_type == "web_search_call":
                    builtin_tool = "web_search"
                elif raw_item_type == "file_search_call":
                    builtin_tool = "file_search"
                elif raw_item_type == "code_interpreter_call":
                    builtin_tool = "code_interpreter"
                elif raw_item_type == "image_generation_call":
                    builtin_tool = "image_generation"
                elif inferred in {
                    "web_search",
                    "file_search",
                    "code_interpreter",
                    "image_generation",
                }:
                    builtin_tool = inferred

                if builtin_tool:
                    tool_type = cast(ToolType, builtin_tool)

            state = self._tool_state.setdefault(tool_call_id, _ToolState(tool_type=tool_type))
            if state.tool_type == "function" and tool_type != "function":
                state.tool_type = tool_type
            state.tool_name = tool_name
            if tool_type == "mcp":
                state.server_label = (
                    _coerce_str((raw_item or {}).get("server_label"))
                    or _coerce_str((raw_item or {}).get("server"))
                    or state.server_label
                )

            if tool_type == "web_search":
                self._last_web_search_tool_call_id = tool_call_id
                action = _as_dict((raw_item or {}).get("action"))
                query = _coerce_str((action or {}).get("query"))
                if query:
                    state.query = query
                raw_status = _coerce_str((raw_item or {}).get("status"))
                if raw_status in {"in_progress", "searching", "completed"}:
                    state.last_status = state.last_status or raw_status

            if tool_type == "file_search":
                queries = (raw_item or {}).get("queries")
                if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                    state.file_search_queries = [q for q in queries if q]

            if event.run_item_name == "mcp_approval_requested" and tool_type == "mcp":
                if state.last_status != "awaiting_approval":
                    state.last_status = "awaiting_approval"
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=McpTool(
                                tool_type="mcp",
                                tool_call_id=tool_call_id,
                                status="awaiting_approval",
                                tool_name=tool_name,
                                server_label=state.server_label,
                            ),
                        )
                    )

            if event.run_item_name == "tool_called" and tool_type == "function":
                if state.last_status != "in_progress":
                    state.last_status = "in_progress"
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=FunctionTool(
                                tool_type="function",
                                tool_call_id=tool_call_id,
                                status="in_progress",
                                name=tool_name,
                            ),
                        )
                    )

            if event.run_item_name == "tool_called" and tool_type == "mcp":
                if state.last_status != "in_progress":
                    state.last_status = "in_progress"
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=McpTool(
                                tool_type="mcp",
                                tool_call_id=tool_call_id,
                                status="in_progress",
                                tool_name=tool_name,
                                server_label=state.server_label,
                            ),
                        )
                    )

            if event.run_item_name == "tool_output":
                output = payload.get("output")
                if output is None:
                    output = payload.get("content")
                if output is None and isinstance(raw_item, dict):
                    output = raw_item.get("output")
                    if output is None:
                        output = raw_item.get("content")

                if tool_type == "web_search" and output is not None:
                    urls = [u for u in _extract_urls(output) if u]
                    if urls:
                        prior = state.sources or []
                        merged_sources = [*prior, *[u for u in urls if u not in prior]]
                        state.sources = merged_sources

                if tool_type in {"function", "mcp"} and output is not None:
                    safe_output = AgentStreamEvent._strip_unserializable(output)
                    sanitized_output, notices = _sanitize_json(
                        safe_output,
                        path="output",
                        max_string_chars=8_000,
                    )
                    out.append(
                        ToolOutputEvent(
                            **_base_kwargs(kind="tool.output", notices=notices or None),
                            tool_call_id=tool_call_id,
                            tool_type=tool_type,
                            output=sanitized_output,
                        )
                    )

                if tool_type == "function":
                    state.last_status = "completed"
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=FunctionTool(
                                tool_type="function",
                                tool_call_id=tool_call_id,
                                status="completed",
                                name=tool_name,
                            ),
                        )
                    )
                elif tool_type == "mcp":
                    state.last_status = "completed"
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=McpTool(
                                tool_type="mcp",
                                tool_call_id=tool_call_id,
                                status="completed",
                                tool_name=tool_name,
                                server_label=state.server_label,
                            ),
                        )
                    )
                elif tool_type == "web_search":
                    status = _as_search_status(state.last_status or "completed")
                    out.append(
                        ToolStatusEvent(
                            **_base_kwargs(kind="tool.status"),
                            tool=WebSearchTool(
                                tool_type="web_search",
                                tool_call_id=tool_call_id,
                                status=status,
                                query=state.query,
                                sources=state.sources,
                            ),
                        )
                    )

        # ----- Terminal projection -----
        if event.is_terminal:
            final_status: FinalStatus = "completed"
            if self._refusal_text:
                final_status = "refused"
            elif self._lifecycle_status in {"failed", "incomplete", "cancelled"}:
                final_status = cast(FinalStatus, self._lifecycle_status)
            elif event.response_text is None and event.structured_output is None:
                final_status = "incomplete"

            out.append(
                FinalEvent(
                    **_base_kwargs(kind="final"),
                    final=FinalPayload(
                        status=final_status,
                        response_text=event.response_text,
                        structured_output=event.structured_output,
                        reasoning_summary_text=self._reasoning_summary_text or None,
                        refusal_text=self._refusal_text or None,
                        attachments=list(self._attachments),
                        usage=_usage_to_public(event.usage),
                    ),
                )
            )
            self._terminal_emitted = True

        return out

    def project_error(
        self,
        *,
        conversation_id: str,
        response_id: str | None,
        agent: str | None,
        workflow_meta: Mapping[str, Any] | None,
        code: str | None,
        message: str,
        source: Literal["provider", "server"],
        is_retryable: bool,
        server_timestamp: str | None = None,
    ) -> ErrorEvent:
        ts = server_timestamp or _now_iso()
        workflow = _workflow_context_from_meta(workflow_meta)
        self._event_id += 1
        self._terminal_emitted = True
        return ErrorEvent(
            schema=PUBLIC_SSE_SCHEMA_VERSION,
            kind="error",
            event_id=self._event_id,
            stream_id=self.stream_id,
            server_timestamp=ts,
            conversation_id=conversation_id,
            response_id=response_id,
            agent=agent,
            workflow=workflow,
            error=ErrorPayload(
                code=code,
                message=message,
                source=source,
                is_retryable=is_retryable,
            ),
        )

    def _chunk_base64(
        self,
        *,
        target: ChunkTarget,
        next_base_kwargs: Callable[[str], Mapping[str, Any]],
        b64: str,
    ) -> Sequence[Any]:
        chunks: list[Any] = []
        idx = 0
        chunk_index = 0
        while idx < len(b64):
            part = b64[idx : idx + self.max_chunk_chars]
            chunks.append(
                ChunkDeltaEvent(
                    **next_base_kwargs("chunk.delta"),
                    target=target,
                    encoding="base64",
                    chunk_index=chunk_index,
                    data=part,
                )
            )
            idx += self.max_chunk_chars
            chunk_index += 1
        chunks.append(
            ChunkDoneEvent(
                **next_base_kwargs("chunk.done"),
                target=target,
            )
        )
        return chunks


__all__ = ["PublicStreamProjector"]
