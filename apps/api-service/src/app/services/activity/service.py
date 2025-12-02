"""Activity/Audit log service with validation and optional streaming."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid4

from app.domain.activity import (
    ActivityEvent,
    ActivityEventFilters,
    ActivityEventPage,
    ActivityEventRepository,
    ActorType,
    StatusType,
)
from app.observability.metrics import ACTIVITY_EVENTS_TOTAL, ACTIVITY_STREAM_PUBLISH_TOTAL
from app.services.activity.registry import validate_action


class NullActivityEventRepository(ActivityEventRepository):
    async def record(self, event: ActivityEvent) -> None:  # pragma: no cover - no-op
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


class ActivityService:
    """Validates and persists activity events, then fan-outs to stream if configured."""

    def __init__(
        self,
        repository: ActivityEventRepository | None = None,
        stream_backend: ActivityStreamBackend | None = None,
        *,
        enable_stream: bool = False,
    ) -> None:
        self._repository = repository or NullActivityEventRepository()
        self._stream_backend = stream_backend
        self._enable_stream = enable_stream
        self._logger = logging.getLogger("api-service.services.activity")

    def set_repository(self, repository: ActivityEventRepository) -> None:
        self._repository = repository

    def set_stream_backend(self, backend: ActivityStreamBackend | None, *, enable: bool) -> None:
        self._stream_backend = backend
        self._enable_stream = enable

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


def _stream_key(tenant_id: str) -> str:
    return f"activity:{tenant_id}"


__all__ = ["ActivityService", "ActivityStreamBackend", "NullActivityEventRepository"]


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
