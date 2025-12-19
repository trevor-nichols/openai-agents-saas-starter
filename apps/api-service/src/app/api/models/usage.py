"""Usage counter response models."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class UsageCounterView(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None = None
    period_start: date
    granularity: str
    input_tokens: int
    output_tokens: int
    requests: int
    storage_bytes: int
    updated_at: datetime
