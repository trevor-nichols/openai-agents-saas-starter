from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..streaming import StreamNotice, WorkflowContext


@dataclass(slots=True)
class EventBuilder:
    """Builds base envelopes for public SSE events and allocates event IDs."""

    stream_id: str
    conversation_id: str
    response_id: str | None
    agent: str | None
    workflow: WorkflowContext | None
    scope: Mapping[str, Any] | None
    server_timestamp: str
    schema: str
    next_event_id: Callable[[], int]

    def base(
        self,
        *,
        kind: str,
        provider_seq: int | None = None,
        notices: list[StreamNotice] | None = None,
    ) -> dict[str, Any]:
        base = {
            "schema": self.schema,
            "kind": kind,
            "event_id": self.next_event_id(),
            "stream_id": self.stream_id,
            "server_timestamp": self.server_timestamp,
            "conversation_id": self.conversation_id,
            "response_id": self.response_id,
            "agent": self.agent,
            "workflow": self.workflow,
            "provider_sequence_number": provider_seq,
            "notices": notices,
        }
        if self.scope is not None:
            base["scope"] = self.scope
        return base

    def item(
        self,
        *,
        kind: str,
        item_id: str,
        output_index: int,
        provider_seq: int | None = None,
        notices: list[StreamNotice] | None = None,
    ) -> dict[str, Any]:
        base = self.base(kind=kind, provider_seq=provider_seq, notices=notices)
        base["item_id"] = item_id
        base["output_index"] = output_index
        return base
