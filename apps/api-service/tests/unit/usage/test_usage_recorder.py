import logging
from datetime import UTC, datetime
from typing import cast

import pytest

from app.services.billing.billing_service import BillingService
from app.services.usage.recorder import UsageEntry, UsageRecorder


class FakeBillingService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def record_usage(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None = None,
        period_start: datetime,
        period_end: datetime,
    ) -> None:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "feature_key": feature_key,
                "quantity": quantity,
                "idempotency_key": idempotency_key,
                "period_start": period_start,
                "period_end": period_end,
            }
        )


@pytest.mark.asyncio
async def test_usage_recorder_persists_entries_with_timezone():
    service = FakeBillingService()
    recorder = UsageRecorder(cast(BillingService, service))
    timestamp = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    entry = UsageEntry(
        feature_key="messages",
        quantity=1,
        idempotency_key="usage-1",
        period_start=timestamp,
        period_end=timestamp,
    )

    await recorder.record_batch("tenant-1", [entry])

    assert len(service.calls) == 1
    call = service.calls[0]
    assert call["tenant_id"] == "tenant-1"
    assert call["feature_key"] == "messages"
    assert call["quantity"] == 1
    assert call["idempotency_key"] == "usage-1"
    assert cast(datetime, call["period_start"]).tzinfo is UTC
    assert cast(datetime, call["period_end"]).tzinfo is UTC


@pytest.mark.asyncio
async def test_usage_recorder_skips_when_no_billing_service(caplog):
    recorder = UsageRecorder()
    timestamp = datetime.now(UTC)
    entry = UsageEntry(
        feature_key="messages",
        quantity=1,
        idempotency_key="usage-2",
        period_start=timestamp,
        period_end=timestamp,
    )

    caplog.set_level(logging.DEBUG)
    await recorder.record_batch("tenant-2", [entry])

    # Nothing should crash, and there should be no billing calls to inspect.
    assert "UsageRecorder has no billing service" in caplog.text
