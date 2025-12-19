from __future__ import annotations

import uuid
import hashlib
from typing import cast

import pytest
from starter_contracts.storage.models import StorageObjectRef

from app.api.v1.shared.streaming import LifecycleEvent
from app.bootstrap import get_container
from app.domain.conversation_ledger import ConversationLedgerEventRecord
from app.infrastructure.persistence.conversations.ledger_store import ConversationLedgerStore
from app.services.conversations import ledger_recorder as ledger_module
from app.services.conversations.ledger_recorder import ConversationLedgerRecorder
from app.services.storage.service import StorageService


class _FakeLedgerStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[ConversationLedgerEventRecord]]] = []

    async def add_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationLedgerEventRecord],
    ) -> None:
        self.calls.append((conversation_id, tenant_id, list(events)))


class _FakeStorageService:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []

    async def put_object(self, **kwargs) -> StorageObjectRef:
        object_id = uuid.uuid4()
        self.put_calls.append(dict(kwargs))
        data = kwargs.get("data", b"")
        size_bytes = len(data) if isinstance(data, (bytes, bytearray)) else None
        return StorageObjectRef(
            id=object_id,
            bucket="bucket",
            key=f"obj/{object_id}",
            size_bytes=size_bytes,
            mime_type=cast(str | None, kwargs.get("mime_type")),
            checksum_sha256=cast(str | None, kwargs.get("checksum_sha256")),
            filename=cast(str | None, kwargs.get("filename")),
        )


def _lifecycle_event(*, conversation_id: str) -> LifecycleEvent:
    return LifecycleEvent(
        schema="public_sse_v1",
        kind="lifecycle",
        event_id=1,
        stream_id="stream_test_01",
        server_timestamp="2025-12-17T12:00:00.000Z",
        conversation_id=conversation_id,
        response_id=None,
        agent="triage",
        status="in_progress",
    )


@pytest.mark.asyncio
async def test_ledger_recorder_inlines_small_events() -> None:
    container = get_container()
    assert container.session_factory is not None

    fake_store = _FakeLedgerStore()
    fake_storage = _FakeStorageService()
    recorder = ConversationLedgerRecorder(
        session_factory=container.session_factory,
        storage_service=cast(StorageService, fake_storage),
        store=cast(ConversationLedgerStore, fake_store),
    )

    tenant_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    event = _lifecycle_event(conversation_id=conversation_id)
    await recorder.record_public_events(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        events=[event],
    )

    assert fake_storage.put_calls == [], "Small events should not be spilled to storage"
    assert len(fake_store.calls) == 1
    _, recorded_tenant, events = fake_store.calls[0]
    assert recorded_tenant == tenant_id
    assert len(events) == 1
    stored = events[0]
    assert stored.payload_json is not None
    assert stored.payload_object_id is None
    assert stored.payload_size_bytes > 0
    assert stored.kind == "lifecycle"


@pytest.mark.asyncio
async def test_ledger_recorder_spills_large_events(monkeypatch: pytest.MonkeyPatch) -> None:
    container = get_container()
    assert container.session_factory is not None

    fake_store = _FakeLedgerStore()
    fake_storage = _FakeStorageService()
    recorder = ConversationLedgerRecorder(
        session_factory=container.session_factory,
        storage_service=cast(StorageService, fake_storage),
        store=cast(ConversationLedgerStore, fake_store),
    )

    # Force spill path without generating massive payloads.
    monkeypatch.setattr(ledger_module, "INLINE_PAYLOAD_MAX_BYTES", 1)

    tenant_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    event = _lifecycle_event(conversation_id=conversation_id)
    await recorder.record_public_events(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        events=[event],
    )

    assert len(fake_storage.put_calls) == 1
    call = fake_storage.put_calls[0]
    assert call.get("mime_type") == "application/gzip"
    data = call.get("data")
    assert isinstance(data, (bytes, bytearray))
    checksum = call.get("checksum_sha256")
    assert isinstance(checksum, str) and checksum
    assert hashlib.sha256(bytes(data)).hexdigest() == checksum
    metadata = call.get("metadata")
    assert isinstance(metadata, dict)
    assert metadata.get("content_encoding") == "gzip"

    assert len(fake_store.calls) == 1
    _, _, events = fake_store.calls[0]
    stored = events[0]
    assert stored.payload_json is None
    assert stored.payload_object_id is not None
