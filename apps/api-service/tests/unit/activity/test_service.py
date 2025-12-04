from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, Sequence, cast

import pytest

from app.domain.activity import (
    ActivityEvent,
    ActivityEventFilters,
    ActivityEventPage,
    ActivityLastSeen,
    ActivityReceipt,
    ReceiptStatus,
)
from app.services.activity.service import (
    ActivityService,
    ActivityStreamBackend,
    NullActivityEventRepository,
)


class _FakeRepo(NullActivityEventRepository):
    def __init__(self) -> None:
        self.events: list[ActivityEvent] = []

    async def record(self, event: ActivityEvent) -> None:
        self.events.append(event)

    async def get_event(self, tenant_id: str, event_id: str) -> ActivityEvent | None:
        return next((ev for ev in self.events if ev.id == event_id and ev.tenant_id == tenant_id), None)

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage:
        # Return in insertion order for test determinism
        return ActivityEventPage(items=list(self.events)[:limit], next_cursor=None)


class _FakeInbox:
    def __init__(self, receipts: dict[str, str], unread_count: int) -> None:
        self.receipts = receipts
        self._unread_count = unread_count

    async def upsert_receipt(
        self,
        *,
        tenant_id: str,
        user_id: str,
        event_id: str,
        status: str,
    ) -> ActivityReceipt:
        receipt = ActivityReceipt(
            tenant_id=tenant_id,
            user_id=user_id,
            event_id=event_id,
            status=cast(ReceiptStatus, status),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.receipts[event_id] = status
        return receipt

    async def fetch_receipts(
        self, *, tenant_id: str, user_id: str, event_ids: Sequence[str]
    ) -> dict[str, ActivityReceipt]:
        return {
            event_id: ActivityReceipt(
                tenant_id=tenant_id,
                user_id=user_id,
                event_id=event_id,
                status=cast(ReceiptStatus, status),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for event_id, status in self.receipts.items()
            if event_id in set(event_ids)
        }

    async def get_checkpoint(self, *, tenant_id: str, user_id: str) -> ActivityLastSeen | None:
        return None

    async def upsert_checkpoint(self, **kwargs) -> ActivityLastSeen:
        return ActivityLastSeen(
            tenant_id=kwargs["tenant_id"],
            user_id=kwargs["user_id"],
            last_seen_created_at=datetime.now(UTC),
            last_seen_event_id=kwargs.get("last_seen_event_id"),
            updated_at=datetime.now(UTC),
        )

    async def count_unread_since(
        self,
        *,
        tenant_id: str,
        user_id: str,
        last_seen_created_at,
        last_seen_event_id,
    ) -> int:
        return self._unread_count


class _FakeStream(ActivityStreamBackend):
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self.subscribed = False

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))

    async def subscribe(self, channel: str) -> Any:
        self.subscribed = True
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        class Stream:
            async def next_message(self_inner, timeout: float | None = None) -> str | None:
                try:
                    return await asyncio.wait_for(queue.get(), timeout=timeout)
                except asyncio.TimeoutError:
                    return None

            async def close(self_inner) -> None:
                return None

        return Stream()

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_activity_service_records_and_streams() -> None:
    repo = _FakeRepo()
    backend = _FakeStream()
    service = ActivityService(repository=repo, stream_backend=backend, enable_stream=True)

    event = await service.record(
        tenant_id="tenant-1",
        action="auth.login.success",
        actor_id="user-1",
        actor_type="user",
        metadata={"user_id": "user-1"},
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert repo.events[0].id == event.id
    assert repo.events[0].ip_hash is not None
    assert backend.published, "stream backend should receive payload"


@pytest.mark.asyncio
async def test_list_events_with_dismissed_returns_item_and_excludes_from_unread() -> None:
    repo = _FakeRepo()
    event_unread = ActivityEvent(
        id="00000000-0000-0000-0000-000000000001",
        tenant_id="tenant-1",
        action="test.one",
        created_at=datetime.now(UTC),
    )
    event_dismissed = ActivityEvent(
        id="00000000-0000-0000-0000-000000000002",
        tenant_id="tenant-1",
        action="test.two",
        created_at=datetime.now(UTC),
    )
    await repo.record(event_unread)
    await repo.record(event_dismissed)

    inbox = _FakeInbox(receipts={event_dismissed.id: "dismissed"}, unread_count=1)
    service = ActivityService(repository=repo, inbox_repository=inbox)

    page = await service.list_events_with_state(
        tenant_id="tenant-1",
        user_id="user-1",
        limit=5,
    )

    assert len(page.items) == 2, "Dismissed events should still be returned"
    states = {item.id: item.read_state for item in page.items}
    assert states[event_unread.id] == "unread"
    assert states[event_dismissed.id] == "dismissed"
    assert page.unread_count == 1, "Unread count should exclude dismissed items"
