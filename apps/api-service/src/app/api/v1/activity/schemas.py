"""Pydantic schemas for activity log API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StatusLiteral = Literal["success", "failure", "pending"]
ReadStateLiteral = Literal["unread", "read", "dismissed"]


class ActivityEventItem(BaseModel):
    id: str
    tenant_id: str
    action: str
    created_at: datetime
    actor_id: str | None = None
    actor_type: str | None = None
    actor_role: str | None = None
    object_type: str | None = None
    object_id: str | None = None
    object_name: str | None = None
    status: StatusLiteral
    source: str | None = None
    request_id: str | None = None
    ip_hash: str | None = Field(default=None, description="Hashed IP (if supplied)")
    user_agent: str | None = None
    metadata: dict[str, object] | None = None
    read_state: ReadStateLiteral = "unread"


class ActivityListResponse(BaseModel):
    items: list[ActivityEventItem]
    next_cursor: str | None = None
    unread_count: int = Field(default=0, ge=0)


class ReceiptResponse(BaseModel):
    unread_count: int = Field(default=0, ge=0)
