from __future__ import annotations

import gzip
import json
import uuid
from typing import Any

import pytest

from app.bootstrap import get_container
from app.infrastructure.persistence.conversations.ledger_query_store import ConversationLedgerEventRef
from app.services.conversations.ledger_reader import ConversationLedgerReader
from app.services.storage.service import StorageService


class _FakeStore:
    def __init__(self, ref: ConversationLedgerEventRef) -> None:
        self._ref = ref

    async def list_events_page(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None,
        workflow_run_id: str | None = None,
    ) -> tuple[list[ConversationLedgerEventRef], str | None]:
        return [self._ref], None


class _FakeStorageService:
    def __init__(self, payload_by_id: dict[uuid.UUID, bytes]) -> None:
        self._payload_by_id = payload_by_id

    async def get_object_bytes(self, *, tenant_id: uuid.UUID, object_id: uuid.UUID, **_: Any) -> bytes:
        return self._payload_by_id[object_id]


@pytest.mark.asyncio
async def test_ledger_reader_decodes_spilled_payloads() -> None:
    container = get_container()
    assert container.session_factory is not None

    tenant_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    object_id = uuid.uuid4()

    event_payload = {
        "schema": "public_sse_v1",
        "kind": "lifecycle",
        "event_id": 1,
        "stream_id": "stream_test_01",
        "server_timestamp": "2025-12-17T12:00:00.000Z",
        "conversation_id": str(conversation_id),
        "response_id": None,
        "agent": "triage",
        "status": "completed",
    }
    compressed = gzip.compress(json.dumps(event_payload).encode("utf-8"))

    store = _FakeStore(
        ConversationLedgerEventRef(
            id=1,
            payload_json=None,
            payload_object_id=object_id,
            payload_size_bytes=len(compressed),
        )
    )
    storage = _FakeStorageService({object_id: compressed})

    reader = ConversationLedgerReader(
        session_factory=container.session_factory,
        storage_service=storage_service_cast(storage),
        store=store_cast(store),
    )

    events, next_cursor = await reader.get_events_page(
        tenant_id=str(tenant_id),
        conversation_id=str(conversation_id),
        limit=10,
        cursor=None,
    )

    assert next_cursor is None
    assert len(events) == 1
    dumped = events[0].model_dump(by_alias=True)
    assert dumped["kind"] == "lifecycle"
    assert dumped["conversation_id"] == str(conversation_id)


def store_cast(store: _FakeStore):
    # Cast helper keeps the fake typed loosely without pulling in Protocol typing in test code.
    return store


def storage_service_cast(storage: _FakeStorageService) -> StorageService:
    return storage  # type: ignore[return-value]
