"""Postgres implementation of the tenant settings repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.tenant_settings import (
    BillingContact,
    TenantSettingsRepository,
    TenantSettingsSnapshot,
)
from app.infrastructure.persistence.tenants.models import TenantSettingsModel


class PostgresTenantSettingsRepository(TenantSettingsRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def fetch(self, tenant_id: str) -> TenantSettingsSnapshot | None:
        tenant_uuid = self._parse_tenant_uuid(tenant_id)
        async with self._session_factory() as session:
            record = await session.scalar(
                select(TenantSettingsModel).where(TenantSettingsModel.tenant_id == tenant_uuid)
            )
            if record is None:
                return None
            return self._to_snapshot(tenant_id, record)

    async def upsert(
        self,
        tenant_id: str,
        *,
        billing_contacts: list[BillingContact],
        billing_webhook_url: str | None,
        plan_metadata: dict[str, str],
        flags: dict[str, bool],
    ) -> TenantSettingsSnapshot:
        tenant_uuid = self._parse_tenant_uuid(tenant_id)
        async with self._session_factory() as session:
            record = await session.scalar(
                select(TenantSettingsModel).where(TenantSettingsModel.tenant_id == tenant_uuid)
            )

            payload = {
                "billing_contacts_json": [self._contact_to_json(item) for item in billing_contacts],
                "billing_webhook_url": billing_webhook_url,
                "plan_metadata_json": plan_metadata,
                "flags_json": flags,
            }

            if record is None:
                record = TenantSettingsModel(
                    tenant_id=tenant_uuid,
                    **payload,
                )
                session.add(record)
            else:
                for key, value in payload.items():
                    setattr(record, key, value)
                record.version += 1

            await session.commit()
            await session.refresh(record)
            return self._to_snapshot(tenant_id, record)

    def _to_snapshot(
        self,
        tenant_id: str,
        record: TenantSettingsModel,
    ) -> TenantSettingsSnapshot:
        contacts = [self._contact_from_json(item) for item in record.billing_contacts_json or []]
        return TenantSettingsSnapshot(
            tenant_id=tenant_id,
            billing_contacts=contacts,
            billing_webhook_url=record.billing_webhook_url,
            plan_metadata=dict(record.plan_metadata_json or {}),
            flags=dict(record.flags_json or {}),
            updated_at=record.updated_at,
        )

    @staticmethod
    def _contact_to_json(contact: BillingContact) -> dict[str, Any]:
        return {
            "name": contact.name,
            "email": contact.email,
            "role": contact.role,
            "phone": contact.phone,
            "notify_billing": contact.notify_billing,
        }

    @staticmethod
    def _contact_from_json(payload: dict[str, Any]) -> BillingContact:
        return BillingContact(
            name=str(payload.get("name", "")).strip(),
            email=str(payload.get("email", "")).strip(),
            role=(
                str(payload.get("role")).strip() if payload.get("role") not in (None, "") else None
            ),
            phone=(
                str(payload.get("phone")).strip()
                if payload.get("phone") not in (None, "")
                else None
            ),
            notify_billing=bool(payload.get("notify_billing", True)),
        )

    @staticmethod
    def _parse_tenant_uuid(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError) as exc:  # pragma: no cover - validation handled upstream
            raise ValueError("Tenant identifier is not a valid UUID.") from exc
