"""Service for persisting public_sse_v1 frames to the durable conversation ledger."""

from __future__ import annotations

import gzip
import hashlib
import io
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.shared.streaming import PublicSseEventBase
from app.domain.conversation_ledger import ConversationLedgerEventRecord
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_store import ConversationLedgerStore
from app.services.storage.service import StorageService

INLINE_PAYLOAD_MAX_BYTES = 1 * 1024 * 1024  # 1 MiB
_GZIP_MIME = "application/gzip"


def _parse_server_timestamp(value: str) -> datetime:
    ts = (value or "").strip()
    if not ts:
        return datetime.now(tz=UTC)
    # Projector timestamps use a 'Z' suffix; normalize for stdlib parsing.
    if ts.endswith("Z"):
        ts = f"{ts[:-1]}+00:00"
    parsed = datetime.fromisoformat(ts)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _gzip_deterministic(data: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6, mtime=0) as gz:
        gz.write(data)
    return buf.getvalue()


def _extract_tool_call_id(event: PublicSseEventBase) -> str | None:
    direct = getattr(event, "tool_call_id", None)
    if isinstance(direct, str) and direct:
        return direct
    tool = getattr(event, "tool", None)
    tool_call_id = getattr(tool, "tool_call_id", None)
    return tool_call_id if isinstance(tool_call_id, str) and tool_call_id else None


@dataclass(slots=True)
class ConversationLedgerRecorder:
    session_factory: async_sessionmaker[AsyncSession]
    storage_service: StorageService
    store: ConversationLedgerStore | None = None

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = ConversationLedgerStore(self.session_factory)

    async def record_public_events(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        events: Sequence[PublicSseEventBase],
    ) -> None:
        if not events:
            return

        tenant_uuid = parse_tenant_id(tenant_id)
        conversation_uuid = coerce_conversation_uuid(conversation_id)

        persisted: list[ConversationLedgerEventRecord] = []
        for event in events:
            payload_text = event.model_dump_json(by_alias=True)
            payload_bytes = payload_text.encode("utf-8")
            payload_size_bytes = len(payload_bytes)

            payload_json: dict[str, Any] | None = None
            payload_object_id: uuid.UUID | None = None

            if payload_size_bytes <= INLINE_PAYLOAD_MAX_BYTES:
                dumped = event.model_dump(by_alias=True, mode="json")
                payload_json = dumped if isinstance(dumped, dict) else {"value": dumped}
            else:
                compressed = _gzip_deterministic(payload_bytes)
                compressed_sha256 = _sha256_hex(compressed)
                uncompressed_sha256 = _sha256_hex(payload_bytes)
                obj = await self.storage_service.put_object(
                    tenant_id=tenant_uuid,
                    user_id=None,
                    data=compressed,
                    filename=f"conversation_ledger_event_{event.stream_id}_{event.event_id}.json.gz",
                    mime_type=_GZIP_MIME,
                    agent_key=event.agent,
                    conversation_id=conversation_uuid,
                    checksum_sha256=compressed_sha256,
                    metadata={
                        "schema_version": event.schema_,
                        "kind": getattr(event, "kind", None),
                        "stream_id": event.stream_id,
                        "event_id": event.event_id,
                        "content_type": "application/json",
                        "content_encoding": "gzip",
                        "uncompressed_size_bytes": payload_size_bytes,
                        "uncompressed_sha256": uncompressed_sha256,
                    },
                )
                if obj.id is None:  # pragma: no cover - defensive
                    raise RuntimeError("StorageService returned object without id")
                payload_object_id = obj.id

            workflow_run_id = None
            workflow = getattr(event, "workflow", None)
            if workflow is not None:
                workflow_run_id = getattr(workflow, "workflow_run_id", None)

            persisted.append(
                ConversationLedgerEventRecord(
                    schema_version=event.schema_,
                    kind=getattr(event, "kind", "unknown"),
                    stream_id=event.stream_id,
                    event_id=event.event_id,
                    server_timestamp=_parse_server_timestamp(event.server_timestamp),
                    response_id=event.response_id,
                    agent=event.agent,
                    workflow_run_id=workflow_run_id if isinstance(workflow_run_id, str) else None,
                    provider_sequence_number=event.provider_sequence_number,
                    output_index=getattr(event, "output_index", None),
                    item_id=getattr(event, "item_id", None),
                    content_index=getattr(event, "content_index", None),
                    tool_call_id=_extract_tool_call_id(event),
                    payload_size_bytes=payload_size_bytes,
                    payload_json=payload_json,
                    payload_object_id=payload_object_id,
                )
            )

        store = self.store
        if store is None:  # pragma: no cover - defensive
            raise RuntimeError("ConversationLedgerStore is not configured")
        await store.add_events(conversation_id, tenant_id=tenant_id, events=persisted)


def get_conversation_ledger_recorder() -> ConversationLedgerRecorder:
    from app.bootstrap.container import get_container, wire_conversation_ledger_recorder
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()
    if getattr(container, "conversation_ledger_recorder", None) is None:
        wire_conversation_ledger_recorder(container)
    recorder = container.conversation_ledger_recorder
    if recorder is None:  # pragma: no cover - defensive
        raise RuntimeError("ConversationLedgerRecorder is not configured")
    return recorder


__all__ = [
    "ConversationLedgerRecorder",
    "get_conversation_ledger_recorder",
    "INLINE_PAYLOAD_MAX_BYTES",
]
