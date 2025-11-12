"""Domain models and protocols for platform status snapshots."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

StatusState = Literal["operational", "degraded", "maintenance", "incident"]
IncidentState = Literal["investigating", "identified", "monitoring", "resolved"]
TrendTone = Literal["positive", "neutral", "negative"]


@dataclass(frozen=True)
class StatusOverview:
    """High-level summary surfaced on the marketing status page."""

    state: str
    description: str
    updated_at: datetime


@dataclass(frozen=True)
class ServiceStatusRecord:
    """Current health metadata for a single service surface."""

    name: str
    status: StatusState
    description: str
    owner: str
    last_incident_at: datetime | None


@dataclass(frozen=True)
class IncidentRecord:
    """External-facing incident entry."""

    incident_id: str
    service: str
    occurred_at: datetime
    impact: str
    state: IncidentState


@dataclass(frozen=True)
class UptimeMetric:
    """Rolling uptime or latency trend line item."""

    label: str
    value: str
    helper_text: str
    trend_value: str
    trend_tone: TrendTone


@dataclass(frozen=True)
class PlatformStatusSnapshot:
    """Complete snapshot returned to external consumers."""

    overview: StatusOverview
    services: Sequence[ServiceStatusRecord]
    incidents: Sequence[IncidentRecord]
    uptime_metrics: Sequence[UptimeMetric]
    generated_at: datetime


class PlatformStatusRepository(Protocol):
    """Repository contract for retrieving platform-status snapshots."""

    async def fetch_snapshot(self) -> PlatformStatusSnapshot:
        """Return the latest snapshot to expose externally."""
        ...
