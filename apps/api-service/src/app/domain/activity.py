"""Domain models and contracts for tenant-scoped activity/audit events."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

ActorType = Literal["user", "service", "system"]
StatusType = Literal["success", "failure", "pending"]
ReceiptStatus = Literal["unread", "read", "dismissed"]


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
class ActivityEventWithState(ActivityEvent):
    """Activity event decorated with per-user read/dismiss state."""

    read_state: ReceiptStatus = "unread"


@dataclass(slots=True)
class ActivityEventStatePage:
    """Keyset-paginated collection of events plus unread count for a user."""

    items: list[ActivityEventWithState]
    next_cursor: str | None
    unread_count: int


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

    async def get_event(self, tenant_id: str, event_id: str) -> ActivityEvent | None: ...

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage: ...


@dataclass(slots=True)
class ActivityReceipt:
    """Per-user receipt marking an event's read/dismissed state."""

    tenant_id: str
    user_id: str
    event_id: str
    status: ReceiptStatus
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ActivityLastSeen:
    """Checkpoint for 'mark all read' semantics."""

    tenant_id: str
    user_id: str
    last_seen_created_at: datetime
    last_seen_event_id: str | None
    updated_at: datetime


class ActivityInboxRepository(Protocol):
    """Persistence contract for per-user activity receipts/checkpoints."""

    async def upsert_receipt(
        self,
        *,
        tenant_id: str,
        user_id: str,
        event_id: str,
        status: ReceiptStatus,
    ) -> ActivityReceipt: ...

    async def fetch_receipts(
        self, *, tenant_id: str, user_id: str, event_ids: Sequence[str]
    ) -> dict[str, ActivityReceipt]: ...

    async def upsert_checkpoint(
        self,
        *,
        tenant_id: str,
        user_id: str,
        last_seen_created_at: datetime,
        last_seen_event_id: str | None,
    ) -> ActivityLastSeen: ...

    async def get_checkpoint(self, *, tenant_id: str, user_id: str) -> ActivityLastSeen | None: ...

    async def count_unread_since(
        self,
        *,
        tenant_id: str,
        user_id: str,
        last_seen_created_at: datetime | None,
        last_seen_event_id: str | None,
    ) -> int: ...


__all__ = [
    "ActorType",
    "StatusType",
    "ReceiptStatus",
    "ActivityEvent",
    "ActivityEventPage",
    "ActivityEventWithState",
    "ActivityEventStatePage",
    "ActivityEventFilters",
    "ActivityEventRepository",
    "ActivityReceipt",
    "ActivityLastSeen",
    "ActivityInboxRepository",
]
