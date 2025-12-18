"""Shared helpers for attachment ingestion.

These helpers are used by both chat (AgentService) and workflows. Keep them
provider-agnostic and free of app-layer dependencies beyond the domain models.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from app.domain.ai.models import AgentStreamEvent


def coerce_conversation_uuid(conversation_id: str | None) -> uuid.UUID | None:
    if not conversation_id:
        return None
    try:
        return uuid.UUID(conversation_id)
    except (TypeError, ValueError):
        return uuid.uuid5(uuid.NAMESPACE_URL, f"api-service:conversation:{conversation_id}")


def collect_container_file_citations_from_event(
    event: AgentStreamEvent,
    *,
    seen: set[str] | None = None,
) -> list[Mapping[str, object]]:
    """Extract unique container_file_citation annotations from a stream event.

    We track these during streaming so we can ingest the referenced container
    files into tenant storage after the run completes (aligning persistence with
    the terminal `final` event).
    """

    sources: list[Mapping[str, object]] = []
    if isinstance(event.annotations, list):
        for ann in event.annotations:
            if isinstance(ann, Mapping):
                sources.append(ann)

    tool_call = event.tool_call
    if isinstance(tool_call, Mapping):
        ci = tool_call.get("code_interpreter_call")
        if isinstance(ci, Mapping):
            annotations = ci.get("annotations")
            if isinstance(annotations, list):
                for ann in annotations:
                    if isinstance(ann, Mapping):
                        sources.append(ann)

    out: list[Mapping[str, object]] = []
    dedupe = seen if seen is not None else set()
    for ann in sources:
        if ann.get("type") != "container_file_citation":
            continue
        container_id = ann.get("container_id")
        file_id = ann.get("file_id")
        if not isinstance(container_id, str) or not isinstance(file_id, str):
            continue
        key = f"{container_id}:{file_id}"
        if key in dedupe:
            continue
        dedupe.add(key)
        out.append(ann)
    return out


__all__ = ["coerce_conversation_uuid", "collect_container_file_citations_from_event"]
