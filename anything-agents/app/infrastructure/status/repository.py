"""Infrastructure implementations for platform status repositories."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Final

from app.domain.status import (
    IncidentRecord,
    PlatformStatusRepository,
    PlatformStatusSnapshot,
    ServiceStatusRecord,
    StatusOverview,
    UptimeMetric,
)


class InMemoryStatusRepository(PlatformStatusRepository):
    """Static repository used until real observability feeds are wired."""

    _SERVICES: Final[tuple[ServiceStatusRecord, ...]] = (
        ServiceStatusRecord(
            name="FastAPI backend",
            status="operational",
            description="JWT auth, chat orchestration, billing webhooks, health probes.",
            owner="Platform Foundations",
            last_incident_at=datetime(2025, 10, 31, tzinfo=UTC),
        ),
        ServiceStatusRecord(
            name="Next.js frontend",
            status="operational",
            description="App Router shell, marketing pages, and server actions.",
            owner="Product Experience",
            last_incident_at=datetime(2025, 10, 18, tzinfo=UTC),
        ),
        ServiceStatusRecord(
            name="Billing event stream",
            status="degraded",
            description="Redis-backed SSE transport for plan, invoice, and usage events.",
            owner="Revenue Engineering",
            last_incident_at=datetime(2025, 11, 8, tzinfo=UTC),
        ),
        ServiceStatusRecord(
            name="Agent chat workspace",
            status="operational",
            description="OpenAI Agents SDK integration, tool metadata, conversation storage.",
            owner="Agent Experience",
            last_incident_at=datetime(2025, 9, 30, tzinfo=UTC),
        ),
    )

    _INCIDENTS: Final[tuple[IncidentRecord, ...]] = (
        IncidentRecord(
            incident_id="redis-maintenance-2025-11-08",
            service="Billing event stream",
            occurred_at=datetime(2025, 11, 8, 13, 0, tzinfo=UTC),
            impact="Degraded throughput during Redis maintenance.",
            state="resolved",
        ),
        IncidentRecord(
            incident_id="postgres-upgrade-2025-10-31",
            service="FastAPI backend",
            occurred_at=datetime(2025, 10, 31, 22, 0, tzinfo=UTC),
            impact="Readiness probe flaps due to Postgres upgrade.",
            state="resolved",
        ),
        IncidentRecord(
            incident_id="cdn-miss-2025-10-18",
            service="Next.js frontend",
            occurred_at=datetime(2025, 10, 18, 16, 30, tzinfo=UTC),
            impact="Static asset cache miss triggered elevated error rates.",
            state="resolved",
        ),
    )

    _UPTIME_METRICS: Final[tuple[UptimeMetric, ...]] = (
        UptimeMetric(
            label="30-day API uptime",
            value="99.97%",
            helper_text="Validated via managed uptime monitors.",
            trend_value="↑ stable",
            trend_tone="positive",
        ),
        UptimeMetric(
            label="Chat latency p95",
            value="2.4s",
            helper_text="Measured end-to-end via Playwright journeys.",
            trend_value="↔ baseline",
            trend_tone="neutral",
        ),
        UptimeMetric(
            label="Billing SSE availability",
            value="99.3%",
            helper_text="Includes Redis maintenance windows.",
            trend_value="↓ watch",
            trend_tone="negative",
        ),
    )

    def __init__(self) -> None:
        self._overview_description = "FastAPI, Next.js, and background workers are healthy."

    async def fetch_snapshot(self) -> PlatformStatusSnapshot:
        now = datetime.now(UTC)
        overview = StatusOverview(
            state="All systems operational",
            description=self._overview_description,
            updated_at=now,
        )

        services = list(self._SERVICES)
        incidents = list(self._INCIDENTS)
        metrics = list(self._UPTIME_METRICS)

        return PlatformStatusSnapshot(
            overview=overview,
            services=services,
            incidents=incidents,
            uptime_metrics=metrics,
            generated_at=now,
        )
