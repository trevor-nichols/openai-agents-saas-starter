"""Usage recording helpers for agent interactions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.domain.ai import AgentRunUsage
from app.infrastructure.persistence.auth.models import UsageCounterGranularity
from app.services.usage_counters import UsageCounterService, get_usage_counter_service
from app.services.usage_recorder import UsageEntry, UsageRecorder


class UsageService:
    """Translates agent run usage into billable usage entries."""

    def __init__(
        self,
        recorder: UsageRecorder | None,
        usage_counters: UsageCounterService | None = None,
    ) -> None:
        self._recorder = recorder
        self._usage_counters = usage_counters or get_usage_counter_service()

    async def record(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        response_id: str | None,
        usage: AgentRunUsage | None,
    ) -> None:
        if not self._recorder:
            return
        timestamp = datetime.now(UTC)
        base_key = response_id or f"{conversation_id}:{uuid.uuid4()}"
        entries: list[UsageEntry] = [
            UsageEntry(
                feature_key="messages",
                quantity=1,
                idempotency_key=f"{base_key}:messages",
                period_start=timestamp,
                period_end=timestamp,
            )
        ]

        if usage:
            if usage.input_tokens:
                entries.append(
                    UsageEntry(
                        feature_key="input_tokens",
                        quantity=int(usage.input_tokens),
                        idempotency_key=f"{base_key}:input_tokens",
                        period_start=timestamp,
                        period_end=timestamp,
                    )
                )
            if usage.output_tokens:
                entries.append(
                    UsageEntry(
                        feature_key="output_tokens",
                        quantity=int(usage.output_tokens),
                        idempotency_key=f"{base_key}:output_tokens",
                        period_start=timestamp,
                        period_end=timestamp,
                    )
                )

        await self._recorder.record_batch(tenant_id, entries)
        if self._usage_counters:
            await self._usage_counters.increment(
                tenant_id=UUID(tenant_id),
                user_id=None,
                period_start=timestamp.date(),
                granularity=UsageCounterGranularity.DAY,
                input_tokens=int(usage.input_tokens) if usage and usage.input_tokens else 0,
                output_tokens=int(usage.output_tokens) if usage and usage.output_tokens else 0,
                requests=1,
            )


__all__ = ["UsageService"]
