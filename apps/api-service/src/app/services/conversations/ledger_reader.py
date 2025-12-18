"""Service for replaying persisted public_sse_v1 frames from the durable ledger."""

from __future__ import annotations

import gzip
import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.shared.streaming import PublicSseEvent
from app.infrastructure.persistence.conversations.ids import parse_tenant_id
from app.infrastructure.persistence.conversations.ledger_query_store import (
    ConversationLedgerEventRef,
    ConversationLedgerQueryStore,
)
from app.services.storage.service import StorageService


@dataclass(slots=True)
class ConversationLedgerReader:
    session_factory: async_sessionmaker[AsyncSession]
    storage_service: StorageService
    store: ConversationLedgerQueryStore | None = None

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = ConversationLedgerQueryStore(self.session_factory)

    async def get_events_page(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        workflow_run_id: str | None = None,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[PublicSseEvent], str | None]:
        store = self.store
        if store is None:  # pragma: no cover - defensive
            raise RuntimeError("ConversationLedgerQueryStore is not configured")

        refs, next_cursor = await store.list_events_page(
            conversation_id,
            tenant_id=tenant_id,
            limit=limit,
            cursor=cursor,
            workflow_run_id=workflow_run_id,
        )

        tenant_uuid = parse_tenant_id(tenant_id)
        events: list[PublicSseEvent] = []
        for ref in refs:
            payload = await self._load_payload_dict(tenant_uuid=tenant_uuid, ref=ref)
            events.append(PublicSseEvent.model_validate(payload))

        return events, next_cursor

    async def iter_events_json(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        workflow_run_id: str | None = None,
        cursor: str | None,
        page_size: int = 500,
    ) -> AsyncIterator[str]:
        """Yield raw JSON objects for each persisted ledger event (in order)."""

        store = self.store
        if store is None:  # pragma: no cover - defensive
            raise RuntimeError("ConversationLedgerQueryStore is not configured")

        tenant_uuid = parse_tenant_id(tenant_id)
        next_cursor = cursor
        while True:
            refs, page_cursor = await store.list_events_page(
                conversation_id,
                tenant_id=tenant_id,
                limit=page_size,
                cursor=next_cursor,
                workflow_run_id=workflow_run_id,
            )
            if not refs:
                return

            for ref in refs:
                yield await self._load_payload_json_text(tenant_uuid=tenant_uuid, ref=ref)

            if not page_cursor:
                return
            next_cursor = page_cursor

    async def _load_payload_json_text(
        self,
        *,
        tenant_uuid: uuid.UUID,
        ref: ConversationLedgerEventRef,
    ) -> str:
        if ref.payload_json is not None:
            return json.dumps(ref.payload_json, separators=(",", ":"), ensure_ascii=False)

        if ref.payload_object_id is None:
            raise ValueError("Ledger event has no payload")

        raw = await self.storage_service.get_object_bytes(
            tenant_id=tenant_uuid,
            object_id=ref.payload_object_id,
        )
        decompressed = gzip.decompress(raw)
        return decompressed.decode("utf-8")

    async def _load_payload_dict(
        self,
        *,
        tenant_uuid: uuid.UUID,
        ref: ConversationLedgerEventRef,
    ) -> dict[str, Any]:
        if ref.payload_json is not None:
            if isinstance(ref.payload_json, dict):
                return ref.payload_json
            return {"value": ref.payload_json}

        text = await self._load_payload_json_text(tenant_uuid=tenant_uuid, ref=ref)
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}


def get_conversation_ledger_reader() -> ConversationLedgerReader:
    from app.bootstrap.container import get_container, wire_conversation_ledger_reader
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()
    if getattr(container, "conversation_ledger_reader", None) is None:
        wire_conversation_ledger_reader(container)
    reader = container.conversation_ledger_reader
    if reader is None:  # pragma: no cover - defensive
        raise RuntimeError("ConversationLedgerReader is not configured")
    return reader


__all__ = ["ConversationLedgerReader", "get_conversation_ledger_reader"]
