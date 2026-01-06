from __future__ import annotations

from dataclasses import replace

import pytest

from app.domain.feature_flags import tenant_feature_key, FeatureKey
from app.domain.tenant_settings import (
    BillingContact,
    TenantSettingsConflictError,
    TenantSettingsSnapshot,
)
from app.services.tenant.tenant_settings_service import TenantSettingsService


class _StubTenantSettingsRepository:
    def __init__(self, snapshot: TenantSettingsSnapshot | None = None) -> None:
        self.snapshot = snapshot
        self.last_flags: dict[str, bool] | None = None
        self.last_expected_version: int | None = None
        self.did_upsert = False

    async def fetch(self, tenant_id: str) -> TenantSettingsSnapshot | None:
        return self.snapshot

    async def upsert(
        self,
        tenant_id: str,
        *,
        billing_contacts: list[BillingContact],
        billing_webhook_url: str | None,
        plan_metadata: dict[str, str],
        flags: dict[str, bool],
        expected_version: int | None = None,
    ) -> TenantSettingsSnapshot:
        self.did_upsert = True
        self.last_flags = dict(flags)
        self.last_expected_version = expected_version
        base = self.snapshot or TenantSettingsSnapshot(tenant_id=tenant_id)
        self.snapshot = replace(
            base,
            billing_contacts=billing_contacts,
            billing_webhook_url=billing_webhook_url,
            plan_metadata=plan_metadata,
            flags=flags,
            version=base.version + 1,
        )
        return self.snapshot

    async def patch_flags(
        self,
        tenant_id: str,
        *,
        updates: dict[str, bool | None],
    ) -> TenantSettingsSnapshot:
        base = self.snapshot or TenantSettingsSnapshot(tenant_id=tenant_id)
        merged = dict(base.flags)
        for key, value in updates.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = bool(value)
        self.snapshot = replace(base, flags=merged)
        return self.snapshot


@pytest.mark.asyncio
async def test_update_settings_preserves_reserved_flags() -> None:
    reserved_key = tenant_feature_key(FeatureKey.BILLING)
    repo = _StubTenantSettingsRepository(
        TenantSettingsSnapshot(
            tenant_id="tenant",
            flags={reserved_key: True},
            version=2,
        )
    )
    service = TenantSettingsService(repository=repo)

    await service.update_settings(
        "tenant",
        billing_contacts=[],
        billing_webhook_url=None,
        plan_metadata={},
        flags={reserved_key: False, "beta": True},
        expected_version=2,
    )

    assert repo.last_flags is not None
    assert repo.last_flags[reserved_key] is True
    assert repo.last_flags["beta"] is True


@pytest.mark.asyncio
async def test_update_settings_raises_on_version_conflict() -> None:
    repo = _StubTenantSettingsRepository(
        TenantSettingsSnapshot(
            tenant_id="tenant",
            flags={},
            version=3,
        )
    )
    service = TenantSettingsService(repository=repo)

    with pytest.raises(TenantSettingsConflictError):
        await service.update_settings(
            "tenant",
            billing_contacts=[],
            billing_webhook_url=None,
            plan_metadata={},
            flags={},
            expected_version=1,
        )

    assert repo.did_upsert is False
