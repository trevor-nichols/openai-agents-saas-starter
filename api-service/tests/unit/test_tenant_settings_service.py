"""Unit tests for the tenant settings service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.tenant_settings import BillingContact, TenantSettingsSnapshot
from app.services.tenant.tenant_settings_service import (
    TenantSettingsService,
    TenantSettingsValidationError,
)


@pytest.mark.anyio
async def test_get_settings_returns_default_when_missing() -> None:
    repository = AsyncMock()
    repository.fetch = AsyncMock(return_value=None)
    service = TenantSettingsService(repository=repository)

    snapshot = await service.get_settings("tenant-123")

    repository.fetch.assert_awaited_once_with("tenant-123")
    assert snapshot.tenant_id == "tenant-123"
    assert snapshot.billing_contacts == []
    assert snapshot.plan_metadata == {}


@pytest.mark.anyio
async def test_update_settings_validates_email() -> None:
    repository = AsyncMock()
    service = TenantSettingsService(repository=repository)

    with pytest.raises(TenantSettingsValidationError):
        invalid_contacts: list[dict[str, object]] = [
            {"name": "Example", "email": "invalid"},
        ]
        await service.update_settings(
            "tenant-1",
            billing_contacts=invalid_contacts,
            billing_webhook_url="https://example.com/webhook",
            plan_metadata={},
            flags={},
        )


@pytest.mark.anyio
async def test_update_settings_persists_normalized_payload() -> None:
    repository = AsyncMock()
    repository.upsert = AsyncMock(
        return_value=TenantSettingsSnapshot(
            tenant_id="tenant-5",
            billing_contacts=[
                BillingContact(
                    name="Jane Smith",
                    email="jane@example.com",
                    role="Owner",
                    phone=None,
                    notify_billing=True,
                )
            ],
            billing_webhook_url="https://hooks.example.com/billing",
            plan_metadata={"plan": "enterprise"},
            flags={"beta": True},
            updated_at=datetime.now(UTC),
        )
    )
    service = TenantSettingsService(repository=repository)

    contacts_input: list[dict[str, object]] = [
        {
            "name": "  Jane Smith  ",
            "email": "JANE@example.com",
            "role": "Owner",
            "notify_billing": True,
        }
    ]
    snapshot = await service.update_settings(
        "tenant-5",
        billing_contacts=contacts_input,
        billing_webhook_url="https://hooks.example.com/billing",
        plan_metadata={"plan": "enterprise", "notes": "  priority  "},
        flags={"beta": True},
    )

    assert snapshot.tenant_id == "tenant-5"
    repository.upsert.assert_awaited_once()
    call = repository.upsert.await_args
    assert call is not None
    args = call.kwargs
    assert args["billing_webhook_url"] == "https://hooks.example.com/billing"
    assert args["plan_metadata"] == {"plan": "enterprise", "notes": "priority"}
