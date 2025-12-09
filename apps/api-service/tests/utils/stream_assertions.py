from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Tuple
from urllib.parse import urlsplit, urlunsplit

from app.api.v1.shared.streaming import (
    CodeInterpreterCall,
    FileCitation,
    FileSearchCall,
    FileSearchResult,
    ImageGenerationCall,
    StreamingEvent,
    UrlCitation,
    WebSearchCall,
)


def _strip_query(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _sanitize(obj):
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


def record_stream(events: Sequence[StreamingEvent], path: Path) -> None:
    """Write sanitized streaming events to NDJSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            sanitized = _sanitize(json.loads(event.model_dump_json()))
            f.write(json.dumps(sanitized, ensure_ascii=False))
            f.write("\n")


def maybe_record_stream(events: Sequence[StreamingEvent], *, env_var: str, default_path: Path) -> None:
    dest = os.getenv(env_var)
    if dest is None:
        return
    target = Path(dest or default_path)
    record_stream(events, target)


# ---------- Assertion helpers ----------


def assert_common_stream(events: Sequence[StreamingEvent]) -> None:
    assert events, "Expected at least one streaming event"
    assert events[-1].is_terminal, "Stream must end with a terminal event"

    seqs = [e.sequence_number for e in events if e.sequence_number is not None]
    assert seqs == sorted(seqs), "sequence_number should be monotonically increasing"

    resp_ids = {e.response_id for e in events if e.response_id}
    assert len(resp_ids) <= 1, "response_id changed mid-stream"


def assert_output_schema_persistent(events: Sequence[StreamingEvent]) -> None:
    """Ensure output_schema is present and consistent across streamed events."""
    assert events, "Expected at least one streaming event"
    schemas = [e.output_schema for e in events if e.output_schema is not None]
    assert schemas, "output_schema missing from streamed events"
    first = schemas[0]
    for idx, schema in enumerate(schemas):
        assert schema == first, f"output_schema changed at event {idx}"


def assembled_text(events: Iterable[StreamingEvent]) -> str:
    return "".join(e.text_delta or "" for e in events).strip()


def collect_annotations(events: Iterable[StreamingEvent]):
    anns = []
    for e in events:
        anns.extend(e.annotations or [])
    return anns


def collect_tool_calls(events: Iterable[StreamingEvent]):
    calls = []
    for e in events:
        tc = e.tool_call
        if tc:
            calls.append(tc)
    return calls


def _last_status_from_tool(events: Iterable[StreamingEvent], attr: str) -> str | None:
    statuses: List[str] = []
    for e in events:
        tool = None
        if isinstance(e.tool_call, dict):
            tool = e.tool_call.get(attr)
        elif e.tool_call:
            tool = getattr(e.tool_call, attr, None)
        if tool:
            status = tool.get("status") if isinstance(tool, dict) else getattr(tool, "status", None)
            if status:
                statuses.append(status)
    return statuses[-1] if statuses else None


def assert_web_search_expectations(events: Sequence[StreamingEvent]) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "web_search_call")
    assert status == "completed", f"web_search_call did not complete (last={status})"

    citations = [a for a in collect_annotations(events) if isinstance(a, UrlCitation)]
    assert citations, "Expected at least one url_citation annotation"
    assert all(a.url for a in citations), "Citation missing URL"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"
    assert any(a.url in full_text for a in citations), "Response text lacks cited URLs"


def assert_code_interpreter_expectations(events: Sequence[StreamingEvent]) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "code_interpreter_call")
    assert status == "completed", f"code_interpreter_call did not complete (last={status})"

    outputs: List[CodeInterpreterCall] = []
    for e in events:
        ci = None
        if isinstance(e.tool_call, dict):
            ci = e.tool_call.get("code_interpreter_call")
        elif e.tool_call:
            ci = getattr(e.tool_call, "code_interpreter_call", None)
        if isinstance(ci, CodeInterpreterCall):
            if ci.outputs:
                outputs.append(ci)
        elif isinstance(ci, dict) and ci.get("outputs"):
            outputs.append(CodeInterpreterCall(**ci))
    assert outputs, "No code interpreter outputs captured"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"
    assert any(token in full_text for token in ["1.414", "1.41", "1.415", "1.4142"]), "Result not mentioned"


def assert_file_search_expectations(events: Sequence[StreamingEvent], *, expected_store_id: str | None = None) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "file_search_call")
    assert status == "completed", f"file_search_call did not complete (last={status})"

    results: List[FileSearchResult] = []
    for e in events:
        fs = None
        if isinstance(e.tool_call, dict):
            fs = e.tool_call.get("file_search_call")
        elif e.tool_call:
            fs = getattr(e.tool_call, "file_search_call", None)
        if isinstance(fs, FileSearchCall):
            if fs.results:
                results.extend(fs.results)
        elif isinstance(fs, dict) and fs.get("results"):
            results.extend(fs["results"])

    assert results, "Expected file_search_call results"
    if expected_store_id:
        def _vector_store_id(val: FileSearchResult | dict[str, object] | Any) -> str | None:
            if isinstance(val, FileSearchResult):
                return val.vector_store_id
            if isinstance(val, dict):
                candidate = val.get("vector_store_id")
                return str(candidate) if candidate is not None else None
            return None

        assert any(
            _vector_store_id(r) == expected_store_id for r in results
        ), "Results did not reference the expected store"

    citations = [a for a in collect_annotations(events) if isinstance(a, FileCitation)]
    assert citations or results, "No file citations or results captured"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def assert_image_generation_expectations(events: Sequence[StreamingEvent]) -> None:
    assert_common_stream(events)
    status = _last_status_from_tool(events, "image_generation_call")
    assert status in {"completed", "generating"}, f"image_generation_call did not complete (last={status})"

    has_attachments = any(e.attachments for e in events)
    assert has_attachments, "No attachments were stored from the image generation call"

    full_text = assembled_text(events)
    assert full_text, "No assistant text returned"


def load_stream_fixture(path: Path) -> List[StreamingEvent]:
    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return [StreamingEvent.model_validate_json(line) for line in lines]
