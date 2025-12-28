"""Utilities for recording metered usage against tenant subscriptions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.services.billing.billing_service import BillingService
from app.services.billing.errors import BillingError


@dataclass(slots=True)
class UsageEntry:
    """Represents a single metered usage contribution."""

    feature_key: str
    quantity: int
    idempotency_key: str
    period_start: datetime
    period_end: datetime


class UsageRecorder:
    """Facade that persists usage batches through the billing service."""

    def __init__(self, billing_service: BillingService | None = None) -> None:
        self._billing_service = billing_service
        self._logger = logging.getLogger(__name__)

    def set_billing_service(self, service: BillingService) -> None:
        self._billing_service = service

    async def record_batch(self, tenant_id: str, entries: Sequence[UsageEntry]) -> None:
        if not self._billing_service:
            self._logger.debug(
                "UsageRecorder has no billing service; skipping usage batch.",
                extra={"tenant_id": tenant_id, "entry_count": len(entries)},
            )
            return

        for entry in entries:
            if entry.quantity <= 0:
                continue
            period_start = self._ensure_timezone(entry.period_start)
            period_end = self._ensure_timezone(entry.period_end)
            try:
                await self._billing_service.record_usage(
                    tenant_id,
                    feature_key=entry.feature_key,
                    quantity=entry.quantity,
                    idempotency_key=entry.idempotency_key,
                    period_start=period_start,
                    period_end=period_end,
                )
            except BillingError as exc:
                self._logger.warning(
                    "Failed to record usage entry.",
                    extra={
                        "tenant_id": tenant_id,
                        "feature_key": entry.feature_key,
                        "quantity": entry.quantity,
                    },
                    exc_info=exc,
                )

    @staticmethod
    def _ensure_timezone(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


__all__ = ["UsageEntry", "UsageRecorder"]
