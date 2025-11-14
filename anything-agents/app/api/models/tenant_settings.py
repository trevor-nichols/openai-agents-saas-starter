"""Tenant settings request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field

from app.domain.tenant_settings import BillingContact, TenantSettingsSnapshot


class BillingContactModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr
    role: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=64)
    notify_billing: bool = True

    @classmethod
    def from_domain(cls, contact: BillingContact) -> BillingContactModel:
        return cls(
            name=contact.name,
            email=contact.email,
            role=contact.role,
            phone=contact.phone,
            notify_billing=contact.notify_billing,
        )

    def to_domain(self) -> BillingContact:
        return BillingContact(
            name=self.name,
            email=self.email,
            role=self.role,
            phone=self.phone,
            notify_billing=self.notify_billing,
        )


class TenantSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    billing_contacts: list[BillingContactModel]
    billing_webhook_url: AnyHttpUrl | None = None
    plan_metadata: dict[str, str]
    flags: dict[str, bool]
    updated_at: datetime | None = None

    @classmethod
    def from_snapshot(cls, snapshot: TenantSettingsSnapshot) -> TenantSettingsResponse:
        return cls(
            tenant_id=snapshot.tenant_id,
            billing_contacts=[
                BillingContactModel.from_domain(contact)
                for contact in snapshot.billing_contacts
            ],
            billing_webhook_url=cast(AnyHttpUrl | None, snapshot.billing_webhook_url),
            plan_metadata=snapshot.plan_metadata,
            flags=snapshot.flags,
            updated_at=snapshot.updated_at,
        )


class TenantSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    billing_contacts: list[BillingContactModel]
    billing_webhook_url: AnyHttpUrl | None = None
    plan_metadata: dict[str, str]
    flags: dict[str, bool]

    def dict_for_service(self) -> dict[str, Any]:
        return {
            "billing_contacts": [contact.to_domain() for contact in self.billing_contacts],
            "billing_webhook_url": (
                str(self.billing_webhook_url) if self.billing_webhook_url else None
            ),
            "plan_metadata": self.plan_metadata,
            "flags": self.flags,
        }


__all__ = [
    "BillingContactModel",
    "TenantSettingsResponse",
    "TenantSettingsUpdateRequest",
]
