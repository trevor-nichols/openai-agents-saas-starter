"""Activity/Audit log service with validation and optional streaming."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid4

from app.domain.activity import (
    ActivityEvent,
    ActivityEventFilters,
    ActivityEventPage,
    ActivityEventRepository,
    ActivityEventStatePage,
    ActivityEventWithState,
    ActivityInboxRepository,
    ActorType,
    ReceiptStatus,
    StatusType,
)
from app.observability.metrics import ACTIVITY_EVENTS_TOTAL, ACTIVITY_STREAM_PUBLISH_TOTAL
from app.services.activity.registry import validate_action


class NullActivityEventRepository(ActivityEventRepository):
    async def record(self, event: ActivityEvent) -> None:  # pragma: no cover - no-op
        return None

    async def get_event(
        self, tenant_id: str, event_id: str
    ) -> ActivityEvent | None:  # pragma: no cover - no-op
        return None

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage:  # pragma: no cover - no-op
        return ActivityEventPage(items=[], next_cursor=None)


class ActivityStreamBackend:
    async def publish(self, channel: str, message: str) -> None: ...

    async def subscribe(self, channel: str): ...

    async def close(self) -> None: ...


class ActivityLookupError(Exception):
    """Base class for activity lookup failures."""


class InvalidActivityIdError(ActivityLookupError):
    """Raised when an activity id is not a valid UUID."""


class ActivityNotFoundError(ActivityLookupError):
    """Raised when an activity event does not exist for a tenant."""


class ActivityService:
    """Validates and persists activity events, then fan-outs to stream if configured."""

    def __init__(
        self,
        repository: ActivityEventRepository | None = None,
        stream_backend: ActivityStreamBackend | None = None,
        inbox_repository: ActivityInboxRepository | None = None,
        *,
        enable_stream: bool = False,
    ) -> None:
        self._repository = repository or NullActivityEventRepository()
        self._stream_backend = stream_backend
        self._inbox_repository = inbox_repository
        self._enable_stream = enable_stream
        self._logger = logging.getLogger("api-service.services.activity")

    def set_repository(self, repository: ActivityEventRepository) -> None:
        self._repository = repository

    def set_stream_backend(self, backend: ActivityStreamBackend | None, *, enable: bool) -> None:
        self._stream_backend = backend
        self._enable_stream = enable

    def set_inbox_repository(self, repository: ActivityInboxRepository | None) -> None:
        self._inbox_repository = repository

    async def record(
        self,
        *,
        tenant_id: str,
        action: str,
        actor_id: str | None = None,
        actor_type: ActorType | None = None,
        actor_role: str | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        object_name: str | None = None,
        status: StatusType = "success",
        source: str | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: Mapping[str, object] | None = None,
        created_at: datetime | None = None,
    ) -> ActivityEvent:
        validate_action(action, metadata)
        event = ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_id,
            action=action,
            created_at=created_at or datetime.now(UTC),
            actor_id=actor_id,
            actor_type=actor_type,
            actor_role=actor_role,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            status=status,
            source=source,
            request_id=request_id,
            ip_hash=self._hash_ip(ip_address),
            user_agent=user_agent if user_agent else None,
            metadata=metadata,
        )

        try:
            await self._repository.record(event)
            ACTIVITY_EVENTS_TOTAL.labels(event.action, "success").inc()
        except Exception as exc:  # pragma: no cover - defensive
            ACTIVITY_EVENTS_TOTAL.labels(event.action, "failure").inc()
            self._logger.warning("activity.record.failed", exc_info=exc)
            raise

        if self._enable_stream and self._stream_backend:
            await self._publish_stream(event)
        return event

    async def list_events(
        self,
        tenant_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventPage:
        return await self._repository.list_events(
            tenant_id,
            limit=limit,
            cursor=cursor,
            filters=filters,
        )

    async def list_events_with_state(
        self,
        tenant_id: str,
        user_id: str,
        *,
        limit: int,
        cursor: str | None = None,
        filters: ActivityEventFilters | None = None,
    ) -> ActivityEventStatePage:
        if not self._inbox_repository:
            # Fallback gracefully if receipts not configured.
            page = await self.list_events(tenant_id, limit=limit, cursor=cursor, filters=filters)
            items = [
                ActivityEventWithState(
                    id=event.id,
                    tenant_id=event.tenant_id,
                    action=event.action,
                    created_at=event.created_at,
                    actor_id=event.actor_id,
                    actor_type=event.actor_type,
                    actor_role=event.actor_role,
                    object_type=event.object_type,
                    object_id=event.object_id,
                    object_name=event.object_name,
                    status=event.status,
                    source=event.source,
                    request_id=event.request_id,
                    ip_hash=event.ip_hash,
                    user_agent=event.user_agent,
                    metadata=event.metadata,
                    read_state="unread",
                )
                for event in page.items
            ]
            return ActivityEventStatePage(
                items=items,
                next_cursor=page.next_cursor,
                unread_count=len(items),
            )

        page = await self.list_events(tenant_id, limit=limit, cursor=cursor, filters=filters)
        checkpoint = await self._inbox_repository.get_checkpoint(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        receipts = await self._inbox_repository.fetch_receipts(
            tenant_id=tenant_id, user_id=user_id, event_ids=[event.id for event in page.items]
        )

        items_with_state: list[ActivityEventWithState] = []
        for event in page.items:
            read_state: ReceiptStatus = "unread"
            receipt = receipts.get(event.id)
            if receipt:
                read_state = receipt.status
            elif checkpoint and self._at_or_before_checkpoint(event, checkpoint):
                read_state = "read"

            items_with_state.append(
                ActivityEventWithState(
                    id=event.id,
                    tenant_id=event.tenant_id,
                    action=event.action,
                    created_at=event.created_at,
                    actor_id=event.actor_id,
                    actor_type=event.actor_type,
                    actor_role=event.actor_role,
                    object_type=event.object_type,
                    object_id=event.object_id,
                    object_name=event.object_name,
                    status=event.status,
                    source=event.source,
                    request_id=event.request_id,
                    ip_hash=event.ip_hash,
                    user_agent=event.user_agent,
                    metadata=event.metadata,
                    read_state=read_state,
                )
            )

        unread_count = await self._inbox_repository.count_unread_since(
            tenant_id=tenant_id,
            user_id=user_id,
            last_seen_created_at=checkpoint.last_seen_created_at if checkpoint else None,
            last_seen_event_id=checkpoint.last_seen_event_id if checkpoint else None,
        )

        return ActivityEventStatePage(
            items=items_with_state,
            next_cursor=page.next_cursor,
            unread_count=unread_count,
        )

    async def mark_read(self, *, tenant_id: str, user_id: str, event_id: str) -> None:
        await self._ensure_event_for_tenant(tenant_id, event_id)
        if not self._inbox_repository:
            return
        await self._inbox_repository.upsert_receipt(
            tenant_id=tenant_id, user_id=user_id, event_id=event_id, status="read"
        )

    async def dismiss(self, *, tenant_id: str, user_id: str, event_id: str) -> None:
        await self._ensure_event_for_tenant(tenant_id, event_id)
        if not self._inbox_repository:
            return
        await self._inbox_repository.upsert_receipt(
            tenant_id=tenant_id, user_id=user_id, event_id=event_id, status="dismissed"
        )

    async def mark_all_read(
        self,
        *,
        tenant_id: str,
        user_id: str,
        anchor_created_at: datetime | None = None,
        anchor_event_id: str | None = None,
    ) -> None:
        if not self._inbox_repository:
            return
        anchor_created_at = anchor_created_at or datetime.now(UTC)
        await self._inbox_repository.upsert_checkpoint(
            tenant_id=tenant_id,
            user_id=user_id,
            last_seen_created_at=anchor_created_at,
            last_seen_event_id=anchor_event_id,
        )

    async def _ensure_event_for_tenant(self, tenant_id: str, event_id: str) -> ActivityEvent:
        try:
            uuid.UUID(event_id)
        except ValueError as exc:
            raise InvalidActivityIdError("event_id must be a valid UUID") from exc

        event = await self._repository.get_event(tenant_id, event_id)
        if not event:
            raise ActivityNotFoundError(
                f"Activity event {event_id} not found for tenant {tenant_id}"
            )
        return event

    async def subscribe(self, tenant_id: str):
        if not (self._enable_stream and self._stream_backend):
            raise RuntimeError("Activity stream not enabled")
        return await self._stream_backend.subscribe(_stream_key(tenant_id))

    async def _publish_stream(self, event: ActivityEvent) -> None:
        if not self._stream_backend:
            return
        payload = json.dumps(
            {
                "id": event.id,
                "tenant_id": event.tenant_id,
                "action": event.action,
                "created_at": event.created_at.isoformat(),
                "actor_id": event.actor_id,
                "actor_type": event.actor_type,
                "actor_role": event.actor_role,
                "object_type": event.object_type,
                "object_id": event.object_id,
                "object_name": event.object_name,
                "status": event.status,
                "source": event.source,
                "request_id": event.request_id,
                "metadata": event.metadata or {},
                "read_state": "unread",
            }
        )
        try:
            await self._stream_backend.publish(_stream_key(event.tenant_id), payload)
            ACTIVITY_STREAM_PUBLISH_TOTAL.labels("success").inc()
        except Exception as exc:  # pragma: no cover - defensive
            ACTIVITY_STREAM_PUBLISH_TOTAL.labels("failure").inc()
            self._logger.warning("activity.stream.publish_failed", exc_info=exc)

    @staticmethod
    def _hash_ip(ip_address: str | None) -> str | None:
        if not ip_address:
            return None
        digest = hashlib.sha256(ip_address.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def _at_or_before_checkpoint(event: ActivityEvent, checkpoint) -> bool:
        if event.created_at < checkpoint.last_seen_created_at:
            return True
        if event.created_at > checkpoint.last_seen_created_at:
            return False
        if checkpoint.last_seen_event_id is None:
            return True
        try:
            event_uuid = uuid.UUID(event.id)
            checkpoint_uuid = uuid.UUID(checkpoint.last_seen_event_id)
            return event_uuid <= checkpoint_uuid
        except Exception:  # pragma: no cover - defensive
            return True


def _stream_key(tenant_id: str) -> str:
    return f"activity:{tenant_id}"


__all__ = [
    "ActivityService",
    "ActivityStreamBackend",
    "NullActivityEventRepository",
    "ActivityLookupError",
    "InvalidActivityIdError",
    "ActivityNotFoundError",
]


def get_activity_service() -> ActivityService:
    from app.bootstrap.container import get_container

    service = get_container().activity_service
    if service is None:
        service = ActivityService()
        get_container().activity_service = service
    return service


class _ActivityServiceHandle:
    def __getattr__(self, name: str):  # pragma: no cover - passthrough
        return getattr(get_activity_service(), name)


activity_service = _ActivityServiceHandle()


__all__ += ["get_activity_service", "activity_service"]
