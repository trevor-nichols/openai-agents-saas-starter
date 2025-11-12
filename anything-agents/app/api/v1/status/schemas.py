"""Pydantic schemas for platform status endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.status import PlatformStatusSnapshot


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
