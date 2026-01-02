"""Context objects used during fixture seeding."""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.persistence.billing.models import TenantSubscription
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.test_fixtures.schemas import (
    FixtureAssetResult,
    FixtureConversationResult,
    FixtureUserResult,
)


@dataclass(slots=True)
class TenantSeedContext:
    tenant: TenantAccount
    plan_code: str | None
    subscription: TenantSubscription | None
    user_results: dict[str, FixtureUserResult]
    conversation_results: dict[str, FixtureConversationResult]
    asset_results: dict[str, FixtureAssetResult]


__all__ = ["TenantSeedContext"]
