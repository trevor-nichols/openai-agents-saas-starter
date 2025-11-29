"""Service layer orchestrating tenant settings CRUD flows."""

from __future__ import annotations

import re
from dataclasses import asdict
from urllib.parse import urlparse

from app.domain.tenant_settings import (
    BillingContact,
    TenantSettingsRepository,
    TenantSettingsSnapshot,
)


class TenantSettingsError(Exception):
    """Base error for tenant settings operations."""


class TenantSettingsValidationError(TenantSettingsError):
    """Raised when provided settings fail validation."""


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_CONTACTS = 10


class TenantSettingsService:
    """Encapsulates validation and persistence of tenant settings."""

    def __init__(self, repository: TenantSettingsRepository | None = None) -> None:
        self._repository = repository

    def set_repository(self, repository: TenantSettingsRepository) -> None:
        self._repository = repository

    def _require_repository(self) -> TenantSettingsRepository:
        if self._repository is None:
            raise RuntimeError("Tenant settings repository has not been configured.")
        return self._repository

    async def get_settings(self, tenant_id: str) -> TenantSettingsSnapshot:
        snapshot = await self._require_repository().fetch(tenant_id)
        if snapshot:
            return snapshot
        return TenantSettingsSnapshot(tenant_id=tenant_id)

    async def update_settings(
        self,
        tenant_id: str,
        *,
        billing_contacts: list[dict[str, object]] | list[BillingContact],
        billing_webhook_url: str | None,
        plan_metadata: dict[str, object],
        flags: dict[str, object],
    ) -> TenantSettingsSnapshot:
        normalized_contacts = self._normalize_contacts(billing_contacts)
        normalized_metadata = self._normalize_plan_metadata(plan_metadata)
        normalized_flags = self._normalize_flags(flags)
        normalized_webhook = self._normalize_webhook(billing_webhook_url)

        snapshot = await self._require_repository().upsert(
            tenant_id,
            billing_contacts=normalized_contacts,
            billing_webhook_url=normalized_webhook,
            plan_metadata=normalized_metadata,
            flags=normalized_flags,
        )
        return snapshot

    def _normalize_contacts(
        self,
        contacts: list[dict[str, object]] | list[BillingContact] | None,
    ) -> list[BillingContact]:
        if contacts is None:
            return []
        normalized: list[BillingContact] = []
        for contact in contacts:
            if isinstance(contact, BillingContact):
                payload = asdict(contact)
            elif isinstance(contact, dict):
                payload = contact
            else:
                raise TenantSettingsValidationError("Billing contacts must be objects.")
            name = self._coerce_string(payload.get("name"))
            email = self._coerce_string(payload.get("email"))
            role = self._coerce_string(payload.get("role"))
            phone = self._coerce_string(payload.get("phone"))
            notify = bool(payload.get("notify_billing", True))

            if not name:
                raise TenantSettingsValidationError("Billing contacts require a name.")
            if not email or not _EMAIL_PATTERN.match(email):
                raise TenantSettingsValidationError("Billing contacts require a valid email.")

            normalized.append(
                BillingContact(
                    name=name,
                    email=email,
                    role=role if role else None,
                    phone=phone if phone else None,
                    notify_billing=notify,
                )
            )

        if len(normalized) > _MAX_CONTACTS:
            raise TenantSettingsValidationError(
                f"Maximum of {_MAX_CONTACTS} billing contacts supported."
            )
        return normalized

    def _normalize_plan_metadata(self, metadata: dict[str, object] | None) -> dict[str, str]:
        if metadata is None:
            return {}
        normalized: dict[str, str] = {}
        for key, value in metadata.items():
            key_str = self._coerce_string(key)
            value_str = self._coerce_string(value)
            if not key_str:
                continue
            normalized[key_str] = value_str
        return normalized

    def _normalize_flags(self, flags: dict[str, object] | None) -> dict[str, bool]:
        if flags is None:
            return {}
        normalized: dict[str, bool] = {}
        for key, value in flags.items():
            key_str = self._coerce_string(key)
            if not key_str:
                continue
            normalized[key_str] = bool(value)
        return normalized

    def _normalize_webhook(self, url: str | None) -> str | None:
        sanitized = self._coerce_string(url)
        if not sanitized:
            return None
        parsed = urlparse(sanitized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise TenantSettingsValidationError("Webhook URL must include http(s) scheme and host.")
        return sanitized

    @staticmethod
    def _coerce_string(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()


def get_tenant_settings_service() -> TenantSettingsService:
    from app.bootstrap.container import get_container

    return get_container().tenant_settings_service


class _TenantSettingsHandle:
    def __getattr__(self, name: str):
        if name == "get_tenant_settings_service":
            return get_tenant_settings_service
        return getattr(get_tenant_settings_service(), name)


tenant_settings_service = _TenantSettingsHandle()


__all__ = [
    "TenantSettingsService",
    "TenantSettingsError",
    "TenantSettingsValidationError",
    "tenant_settings_service",
    "get_tenant_settings_service",
]
