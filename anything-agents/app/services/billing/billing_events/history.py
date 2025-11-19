"""History pagination helpers for billing events."""

from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.persistence.stripe.models import StripeEventStatus
from app.infrastructure.persistence.stripe.repository import StripeEventRepository

from .normalizer import BillingEventNormalizer
from .payloads import BillingEventPayload


@dataclass(slots=True)
class BillingEventHistoryPage:
    items: list[BillingEventPayload]
    next_cursor: str | None


@dataclass(slots=True)
class _HistoryCursor:
    received_at: datetime
    event_id: uuid.UUID


class BillingEventHistoryReader:
    def __init__(self, normalizer: BillingEventNormalizer) -> None:
        self._normalizer = normalizer
        self._repository: StripeEventRepository | None = None

    def configure(self, repository: StripeEventRepository | None) -> None:
        if repository is not None:
            self._repository = repository

    async def list_history(
        self,
        *,
        tenant_id: str,
        limit: int = 25,
        cursor: str | None = None,
        event_type: str | None = None,
        status: StripeEventStatus | str | None = None,
    ) -> BillingEventHistoryPage:
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        repository = self._require_repository()
        cursor_values = self._decode_cursor(cursor) if cursor else None
        repo_status = status.value if isinstance(status, StripeEventStatus) else status
        page_size = max(1, limit)

        fetch_limit = page_size + 1
        events = await repository.list_tenant_events(
            tenant_id=tenant_id,
            limit=fetch_limit,
            cursor_received_at=cursor_values.received_at if cursor_values else None,
            cursor_event_id=cursor_values.event_id if cursor_values else None,
            event_type=event_type,
            status=repo_status,
        )

        trimmed_events = events[:page_size]
        payloads: list[BillingEventPayload] = []
        for record in trimmed_events:
            normalized = self._normalizer.normalize(record, record.payload, None)
            if normalized:
                payloads.append(normalized)

        next_cursor = None
        has_more = len(events) > page_size
        if has_more and trimmed_events:
            tail = trimmed_events[-1]
            next_cursor = self._encode_cursor(tail.received_at, tail.id)

        return BillingEventHistoryPage(items=payloads, next_cursor=next_cursor)

    def _require_repository(self) -> StripeEventRepository:
        if self._repository is None:
            raise RuntimeError(
                "StripeEventRepository is not configured for billing event history service."
            )
        return self._repository

    def _encode_cursor(self, received_at: datetime, event_id: uuid.UUID) -> str:
        payload = json.dumps({"r": received_at.isoformat(), "e": str(event_id)})
        return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")

    def _decode_cursor(self, token: str) -> _HistoryCursor:
        try:
            raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            received_at = datetime.fromisoformat(str(data["r"]))
            event_id = uuid.UUID(str(data["e"]))
        except (KeyError, ValueError, json.JSONDecodeError) as exc:  # pragma: no cover
            raise ValueError("Invalid cursor provided.") from exc
        return _HistoryCursor(received_at=received_at, event_id=event_id)
