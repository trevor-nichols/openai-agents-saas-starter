from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from app.core.settings import Settings
from app.domain.feature_flags import FeatureKey, tenant_feature_key
from app.domain.tenant_settings import BillingContact, TenantSettingsSnapshot
from app.services.feature_flags import FeatureEntitlementService, FeatureFlagService


class _Settings:
    def __init__(self, *, enable_billing: bool, enable_billing_stream: bool) -> None:
        self.enable_billing = enable_billing
        self.enable_billing_stream = enable_billing_stream


class _StubTenantSettingsRepository:
    def __init__(self, snapshot: TenantSettingsSnapshot | None = None) -> None:
        self.snapshot = snapshot
        self.last_flags: dict[str, bool] | None = None

    async def fetch(self, tenant_id: str) -> TenantSettingsSnapshot | None:
        return self.snapshot

    async def patch_flags(
        self,
        tenant_id: str,
        *,
        updates: dict[str, bool | None],
    ) -> TenantSettingsSnapshot:
        merged = dict(self.snapshot.flags if self.snapshot else {})
        for key, value in updates.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = bool(value)
        self.last_flags = dict(merged)
        base = self.snapshot or TenantSettingsSnapshot(tenant_id=tenant_id)
        self.snapshot = replace(base, flags=merged)
        return self.snapshot

    async def upsert(
        self,
        tenant_id: str,
        *,
        billing_contacts,
        billing_webhook_url,
        plan_metadata,
        flags,
        expected_version=None,
    ) -> TenantSettingsSnapshot:
        self.last_flags = dict(flags)
        base = self.snapshot or TenantSettingsSnapshot(tenant_id=tenant_id)
        self.snapshot = replace(
            base,
            billing_contacts=billing_contacts,
            billing_webhook_url=billing_webhook_url,
            plan_metadata=plan_metadata,
            flags=flags,
        )
        return self.snapshot


@pytest.mark.asyncio
async def test_billing_disabled_overrides_tenant_entitlement() -> None:
    repo = _StubTenantSettingsRepository(
        TenantSettingsSnapshot(
            tenant_id="tenant",
            flags={tenant_feature_key(FeatureKey.BILLING): True},
        )
    )
    service = FeatureFlagService(
        repository=repo,
        settings_factory=lambda: cast(
            Settings,
            _Settings(enable_billing=False, enable_billing_stream=True),
        ),
    )

    snapshot = await service.snapshot_for_tenant("tenant")
    assert snapshot.billing_enabled is False
    assert snapshot.billing_stream_enabled is False


@pytest.mark.asyncio
async def test_billing_inherits_global_when_no_tenant_override() -> None:
    repo = _StubTenantSettingsRepository(TenantSettingsSnapshot(tenant_id="tenant"))
    service = FeatureFlagService(
        repository=repo,
        settings_factory=lambda: cast(
            Settings,
            _Settings(enable_billing=True, enable_billing_stream=False),
        ),
    )

    snapshot = await service.snapshot_for_tenant("tenant")
    assert snapshot.billing_enabled is True
    assert snapshot.billing_stream_enabled is False


@pytest.mark.asyncio
async def test_tenant_override_can_disable_billing() -> None:
    repo = _StubTenantSettingsRepository(
        TenantSettingsSnapshot(
            tenant_id="tenant",
            flags={tenant_feature_key(FeatureKey.BILLING): False},
        )
    )
    service = FeatureFlagService(
        repository=repo,
        settings_factory=lambda: cast(
            Settings,
            _Settings(enable_billing=True, enable_billing_stream=True),
        ),
    )

    snapshot = await service.snapshot_for_tenant("tenant")
    assert snapshot.billing_enabled is False
    assert snapshot.billing_stream_enabled is False


@pytest.mark.asyncio
async def test_billing_stream_requires_billing() -> None:
    repo = _StubTenantSettingsRepository(TenantSettingsSnapshot(tenant_id="tenant"))
    service = FeatureFlagService(
        repository=repo,
        settings_factory=lambda: cast(
            Settings,
            _Settings(enable_billing=True, enable_billing_stream=True),
        ),
    )

    snapshot = await service.snapshot_for_tenant("tenant")
    assert snapshot.billing_enabled is True
    assert snapshot.billing_stream_enabled is True


@pytest.mark.asyncio
async def test_entitlement_updates_set_and_clear_flags() -> None:
    repo = _StubTenantSettingsRepository(
        TenantSettingsSnapshot(tenant_id="tenant", flags={"beta_features": True})
    )
    service = FeatureEntitlementService(repository=repo)

    updated = await service.update_entitlements(
        "tenant", updates={FeatureKey.BILLING: True}
    )
    assert updated.entitlements[FeatureKey.BILLING] is True
    assert repo.last_flags is not None
    assert repo.last_flags[tenant_feature_key(FeatureKey.BILLING)] is True

    cleared = await service.update_entitlements(
        "tenant", updates={FeatureKey.BILLING: None}
    )
    assert FeatureKey.BILLING not in cleared.entitlements
    assert repo.last_flags is not None
    assert tenant_feature_key(FeatureKey.BILLING) not in repo.last_flags


@pytest.mark.asyncio
async def test_entitlement_updates_preserve_other_settings() -> None:
    contacts = [BillingContact(name="Ava", email="ava@example.com", notify_billing=True)]
    snapshot = TenantSettingsSnapshot(
        tenant_id="tenant",
        billing_contacts=contacts,
        plan_metadata={"plan": "pro"},
        flags={"beta_features": True},
    )
    repo = _StubTenantSettingsRepository(snapshot)
    service = FeatureEntitlementService(repository=repo)

    await service.update_entitlements("tenant", updates={FeatureKey.BILLING: True})

    assert repo.snapshot is not None
    assert repo.snapshot.billing_contacts == contacts
    assert repo.snapshot.plan_metadata == {"plan": "pro"}
