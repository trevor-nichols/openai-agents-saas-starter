"""Pydantic schemas for platform status endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.status import (
    PlatformStatusSnapshot,
    StatusSubscription,
    StatusSubscriptionListResult,
)


class StatusOverviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: str = Field(description="Human-readable health summary.")
    description: str = Field(description="Contextual description displayed on the status page.")
    updated_at: datetime = Field(description="Timestamp of the last health aggregation.")


class ServiceStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Service or subsystem name.")
    status: str = Field(description="Operational status label.")
    description: str = Field(description="Short explanation of the service scope.")
    owner: str = Field(description="Team responsible for the service.")
    last_incident_at: datetime | None = Field(
        default=None,
        description="Timestamp of the most recent incident involving the service.",
    )


class IncidentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str = Field(description="Internal incident identifier.")
    service: str = Field(description="Impacted service name.")
    occurred_at: datetime = Field(description="When the incident was recorded.")
    impact: str = Field(description="External-facing description of the impact.")
    state: str = Field(description="Current incident lifecycle state.")


class UptimeMetricSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    value: str
    helper_text: str
    trend_value: str
    trend_tone: str


class PlatformStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime = Field(description="Server-side generation timestamp for the snapshot.")
    overview: StatusOverviewSchema
    services: list[ServiceStatusSchema]
    incidents: list[IncidentSchema]
    uptime_metrics: list[UptimeMetricSchema]

    @classmethod
    def from_snapshot(cls, snapshot: PlatformStatusSnapshot) -> PlatformStatusResponse:
        return cls.model_validate(snapshot)


class StatusSubscriptionCreateRequest(BaseModel):
    channel: Literal["email", "webhook"]
    target: str
    severity_filter: Literal["all", "major", "maintenance"] | None = Field(
        default="major",
        description="Incident severity filter.",
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata labels.")


class StatusSubscriptionResponse(BaseModel):
    id: UUID
    channel: str
    severity_filter: str
    status: str
    target_masked: str
    tenant_id: UUID | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    webhook_secret: str | None = Field(
        default=None,
        description="Signing secret for webhook deliveries (returned on creation only).",
    )

    @classmethod
    def from_domain(cls, record: StatusSubscription) -> StatusSubscriptionResponse:
        return cls(
            id=record.id,
            channel=record.channel,
            severity_filter=record.severity_filter,
            status=record.status,
            target_masked=record.target_masked,
            tenant_id=record.tenant_id,
            created_by=record.created_by,
            created_at=record.created_at,
            updated_at=record.updated_at,
            webhook_secret=None,
        )


class StatusSubscriptionListResponse(BaseModel):
    items: list[StatusSubscriptionResponse]
    next_cursor: str | None = None

    @classmethod
    def from_result(cls, result: StatusSubscriptionListResult) -> StatusSubscriptionListResponse:
        return cls(
            items=[StatusSubscriptionResponse.from_domain(item) for item in result.items],
            next_cursor=result.next_cursor,
        )


class StatusSubscriptionVerifyRequest(BaseModel):
    token: str = Field(description="Email verification token.")


class StatusSubscriptionChallengeRequest(BaseModel):
    token: str = Field(description="Webhook challenge token.")


class StatusIncidentResendRequest(BaseModel):
    severity: Literal["all", "major", "maintenance"] = Field(
        default="major",
        description="Incident severity used to filter subscriptions.",
    )
    tenant_id: UUID | None = Field(
        default=None,
        description="Restrict delivery to a specific tenant context.",
    )


class StatusIncidentResendResponse(BaseModel):
    dispatched: int = Field(description="Number of subscriptions notified.")

