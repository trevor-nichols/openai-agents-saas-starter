"""Domain primitives for the durable conversation ledger.

The ledger persists the public SSE frames that the frontend consumes so we can
replay the *exact* UI transcript (including tool components) later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ConversationLedgerEventRecord:
    """Single persisted public_sse_v1 frame (inline JSON or spilled to object storage)."""

    schema_version: str
    kind: str
    stream_id: str
    event_id: int
    server_timestamp: datetime

    response_id: str | None
    agent: str | None
    workflow_run_id: str | None
    provider_sequence_number: int | None

    output_index: int | None
    item_id: str | None
    content_index: int | None
    tool_call_id: str | None

    payload_size_bytes: int
    payload_json: dict[str, Any] | None = None
    payload_object_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if self.payload_json is None and self.payload_object_id is None:
            raise ValueError(
                "ConversationLedgerEventRecord requires payload_json or payload_object_id"
            )


__all__ = ["ConversationLedgerEventRecord"]
