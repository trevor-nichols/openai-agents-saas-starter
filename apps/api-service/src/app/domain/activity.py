"""Domain models and contracts for tenant-scoped activity/audit events."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

ActorType = Literal["user", "service", "system"]
StatusType = Literal["success", "failure", "pending"]


@dataclass(slots=True)
class ActivityEvent:
    """Canonical audit/event record captured across the platform."""

    id: str
    tenant_id: str
    action: str
    created_at: datetime
    actor_id: str | None = None
    actor_type: ActorType | None = None
    actor_role: str | None = None
    object_type: str | None = None
    object_id: str | None = None
    object_name: str | None = None
    status: StatusType = "success"
    source: str | None = None
    request_id: str | None = None
    ip_hash: str | None = None
    user_agent: str | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(slots=True)
class ActivityEventPage:
    """Keyset-paginated collection of activity events."""

    items: list[ActivityEvent]
    next_cursor: str | None


@dataclass(slots=True)
class ActivityEventFilters:
    """Filter parameters supported by the repository list call."""

    action: str | None = None
    actor_id: str | None = None
    object_type: str | None = None
    object_id: str | None = None
    status: StatusType | None = None
    request_id: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class ActivityEventRepository(Protocol):
    """Persistence contract for activity events."""

    async def record(self, event: ActivityEvent) -> None: ...

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage: ...


__all__ = [
    "ActorType",
    "StatusType",
    "ActivityEvent",
    "ActivityEventPage",
    "ActivityEventFilters",
    "ActivityEventRepository",
]
