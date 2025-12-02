from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app.domain.activity import ActivityEvent, ActivityEventFilters, ActivityEventPage
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

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage:
        return ActivityEventPage(items=[], next_cursor=None)


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
