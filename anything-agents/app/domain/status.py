"""Domain models and protocols for platform status snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

StatusState = Literal["operational", "degraded", "maintenance", "incident"]
IncidentState = Literal["investigating", "identified", "monitoring", "resolved"]
TrendTone = Literal["positive", "neutral", "negative"]
SubscriptionChannel = Literal["email", "webhook"]
SubscriptionSeverity = Literal["all", "major", "maintenance"]
SubscriptionStatus = Literal["pending_verification", "active", "revoked"]


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


@dataclass(frozen=True)
class StatusSubscription:
    """Domain representation of a status-alert subscription."""

    id: UUID
    channel: SubscriptionChannel
    target_masked: str
    severity_filter: SubscriptionSeverity
    status: SubscriptionStatus
    tenant_id: UUID | None
    metadata: Mapping[str, object]
    created_by: str
    created_at: datetime
    updated_at: datetime
    verification_expires_at: datetime | None
    revoked_at: datetime | None
    unsubscribe_token_hash: str | None


@dataclass(frozen=True)
class StatusSubscriptionCreate:
    """Payload required to persist a new subscription."""

    channel: SubscriptionChannel
    target: str
    target_hash: str
    target_masked: str
    severity_filter: SubscriptionSeverity
    metadata: Mapping[str, object]
    tenant_id: UUID | None
    created_by: str
    verification_token_hash: str | None
    verification_expires_at: datetime | None
    challenge_token_hash: str | None
    webhook_secret: str | None
    status: SubscriptionStatus
    unsubscribe_token_hash: str | None
    unsubscribe_token: str | None


@dataclass(frozen=True)
class StatusSubscriptionListResult:
    """Paginated list of subscriptions."""

    items: Sequence[StatusSubscription]
    next_cursor: str | None


class StatusSubscriptionRepository(Protocol):
    """Persistence contract for status subscriptions."""

    async def create(self, payload: StatusSubscriptionCreate) -> StatusSubscription:
        ...

    async def find_by_id(self, subscription_id: UUID) -> StatusSubscription | None:
        ...

    async def find_by_verification_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        ...

    async def find_by_challenge_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        ...

    async def find_by_unsubscribe_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        ...

    async def list_subscriptions(
        self,
        *,
        tenant_id: UUID | None,
        status: SubscriptionStatus | None,
        limit: int,
        cursor: str | None,
    ) -> StatusSubscriptionListResult:
        ...

    async def mark_active(self, subscription_id: UUID) -> StatusSubscription | None:
        ...

    async def mark_revoked(
        self,
        subscription_id: UUID,
        *,
        reason: str | None = None,
    ) -> StatusSubscription | None:
        ...

    async def update_verification_token(
        self,
        subscription_id: UUID,
        *,
        token_hash: str | None,
        expires_at: datetime | None,
    ) -> StatusSubscription | None:
        ...

    async def get_delivery_target(self, subscription_id: UUID) -> str | None:
        ...

    async def get_webhook_secret(self, subscription_id: UUID) -> str | None:
        ...

    async def find_active_by_target(
        self,
        *,
        channel: SubscriptionChannel,
        target_hash: str,
        severity_filter: SubscriptionSeverity,
        tenant_id: UUID | None,
    ) -> StatusSubscription | None:
        ...

    async def get_unsubscribe_token(self, subscription_id: UUID) -> str | None:
        ...

    async def set_unsubscribe_token(
        self,
        subscription_id: UUID,
        *,
        token_hash: str,
        token: str,
    ) -> bool:
        ...
