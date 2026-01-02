"""Schemas for deterministic test fixture specifications and results."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from app.domain.assets import AssetSourceTool, AssetType
from app.domain.platform_roles import PlatformRole
from app.domain.tenant_roles import TenantRole


class FixtureConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str = Field(min_length=1)


class FixtureConversation(BaseModel):
    key: str = Field(min_length=1)
    agent_entrypoint: str = Field(default="default", min_length=1)
    status: Literal["active", "archived"] = "active"
    user_email: EmailStr | None = None
    messages: list[FixtureConversationMessage] = Field(default_factory=list)


class FixtureUsageEntry(BaseModel):
    feature_key: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit: str = Field(default="requests", min_length=1)
    period_start: datetime
    period_end: datetime | None = None
    idempotency_key: str | None = None

    @field_validator("period_end")
    @classmethod
    def _ensure_period_order(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        if value is None:
            return None
        period_start = info.data.get("period_start")
        if not isinstance(period_start, datetime):
            return value
        if value < period_start:
            raise ValueError("period_end cannot be earlier than period_start")
        return value


class FixtureUsageCounter(BaseModel):
    period_start: date
    granularity: Literal["day", "month"] = "day"
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    requests: int = Field(default=0, ge=0)
    storage_bytes: int = Field(default=0, ge=0)
    user_email: EmailStr | None = None


class FixtureAsset(BaseModel):
    key: str = Field(min_length=1)
    asset_type: AssetType = Field(default="file")
    source_tool: AssetSourceTool | None = None
    filename: str = Field(min_length=1)
    mime_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    agent_key: str | None = Field(default=None, max_length=64)
    conversation_key: str | None = None
    message_id: int | None = Field(default=None, ge=1)
    tool_call_id: str | None = None
    response_id: str | None = None
    container_id: str | None = None
    openai_file_id: str | None = None
    user_email: EmailStr | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class FixtureUser(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None
    role: TenantRole = Field(default=TenantRole.ADMIN)
    platform_role: PlatformRole | None = None
    verify_email: bool = True


class FixtureTenant(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    plan_code: str | None = None
    billing_email: EmailStr | None = None
    users: list[FixtureUser] = Field(default_factory=list)
    conversations: list[FixtureConversation] = Field(default_factory=list)
    usage: list[FixtureUsageEntry] = Field(default_factory=list)
    usage_counters: list[FixtureUsageCounter] = Field(default_factory=list)
    assets: list[FixtureAsset] = Field(default_factory=list)


class PlaywrightFixtureSpec(BaseModel):
    tenants: list[FixtureTenant] = Field(default_factory=list)


class FixtureUserResult(BaseModel):
    user_id: str
    role: TenantRole


class FixtureConversationResult(BaseModel):
    conversation_id: str
    status: str


class FixtureAssetResult(BaseModel):
    asset_id: str
    storage_object_id: str


class FixtureTenantResult(BaseModel):
    tenant_id: str
    plan_code: str | None
    users: dict[str, FixtureUserResult]
    conversations: dict[str, FixtureConversationResult]
    assets: dict[str, FixtureAssetResult] = Field(default_factory=dict)


class FixtureApplyResult(BaseModel):
    tenants: dict[str, FixtureTenantResult]
    generated_at: datetime


__all__ = [
    "FixtureApplyResult",
    "FixtureAsset",
    "FixtureAssetResult",
    "FixtureConversation",
    "FixtureConversationMessage",
    "FixtureConversationResult",
    "FixtureTenant",
    "FixtureTenantResult",
    "FixtureUsageCounter",
    "FixtureUsageEntry",
    "FixtureUser",
    "FixtureUserResult",
    "PlaywrightFixtureSpec",
]
