"""Pydantic models for consent endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConsentRequest(BaseModel):
    policy_key: str = Field(..., max_length=64)
    version: str = Field(..., max_length=32)
    ip_hash: str | None = Field(default=None, max_length=128)
    user_agent_hash: str | None = Field(default=None, max_length=128)


class ConsentView(BaseModel):
    policy_key: str
    version: str
    accepted_at: datetime

