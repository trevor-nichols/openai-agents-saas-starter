"""Notification preference API models."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class NotificationPreferenceRequest(BaseModel):
    channel: str = Field(..., max_length=16)
    category: str = Field(..., max_length=64)
    enabled: bool = True
    tenant_id: UUID | None = None


class NotificationPreferenceView(BaseModel):
    id: UUID
    channel: str
    category: str
    enabled: bool
    tenant_id: UUID | None = None
