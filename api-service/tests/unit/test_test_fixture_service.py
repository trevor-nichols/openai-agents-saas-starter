"""Tests for the deterministic test fixture orchestration service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bootstrap import ApplicationContainer, reset_container, set_container
from app.infrastructure.persistence.auth import models as auth_models
from app.infrastructure.persistence.billing import models as billing_models
from app.infrastructure.persistence.conversations import models as conversation_models
from app.infrastructure.persistence.tenants import models as tenant_models
from app.services.test_fixtures import PlaywrightFixtureSpec, TestFixtureService
from tests.utils.sqlalchemy import create_tables

TABLES: tuple[Table, ...] = cast(
    tuple[Table, ...],
    (
        conversation_models.TenantAccount.__table__,
        auth_models.UserAccount.__table__,
        auth_models.UserProfile.__table__,
        auth_models.PasswordHistory.__table__,
        auth_models.TenantUserMembership.__table__,
        billing_models.BillingPlan.__table__,
        billing_models.PlanFeature.__table__,
        billing_models.TenantSubscription.__table__,
        billing_models.SubscriptionUsage.__table__,
        tenant_models.TenantSettingsModel.__table__,
        conversation_models.AgentConversation.__table__,
        conversation_models.AgentMessage.__table__,
    ),
)


@pytest.mark.asyncio
async def test_apply_spec_seeds_tenant_user_subscription() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda connection: create_tables(connection, TABLES))

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as session:
        session.add_all(_default_plans())
        await session.commit()

    container = ApplicationContainer(session_factory=session_factory)
    set_container(container)
    service = TestFixtureService(container)

    now = datetime.now(UTC)
    spec = PlaywrightFixtureSpec.model_validate(
        {
            "tenants": [
                {
                    "slug": "playwright-starter",
                    "name": "Playwright Starter",
                    "plan_code": "starter",
                    "billing_email": "billing@example.com",
                    "users": [
                        {
                            "email": "admin@example.com",
                            "password": "Playwright123!",
                            "display_name": "Playwright Admin",
                            "role": "owner",
                        }
                    ],
                    "conversations": [
                        {
                            "key": "seeded-conversation",
                            "messages": [
                                {"role": "user", "text": "Hello agent"},
                                {"role": "assistant", "text": "Hello human"},
                            ],
                        }
                    ],
                    "usage": [
                        {
                            "feature_key": "messages",
                            "quantity": 50,
                            "period_start": now.isoformat(),
                        }
                    ],
                }
            ]
        }
    )

    result = await service.apply_spec(spec)
    tenant_result = result.tenants["playwright-starter"]

    async with session_factory() as session:
        tenant = await session.scalar(
            select(conversation_models.TenantAccount).where(
                conversation_models.TenantAccount.slug == "playwright-starter"
            )
        )
        assert tenant is not None
        user = await session.scalar(
            select(auth_models.UserAccount).where(
                auth_models.UserAccount.email == "admin@example.com"
            )
        )
        assert user is not None
        membership = await session.scalar(
            select(auth_models.TenantUserMembership).where(
                auth_models.TenantUserMembership.user_id == user.id
            )
        )
        assert membership is not None
        subscription = await session.scalar(
            select(billing_models.TenantSubscription).where(
                billing_models.TenantSubscription.tenant_id == tenant.id
            )
        )
        assert subscription is not None
        usage = await session.scalar(
            select(billing_models.SubscriptionUsage).where(
                billing_models.SubscriptionUsage.subscription_id == subscription.id
            )
        )
        assert usage is not None
        conversation = await session.scalar(
            select(conversation_models.AgentConversation).where(
                conversation_models.AgentConversation.conversation_key == "seeded-conversation"
            )
        )
        assert conversation is not None

    assert tenant_result.plan_code == "starter"
    assert tenant_result.users["admin@example.com"].user_id
    assert tenant_result.conversations["seeded-conversation"].status == "active"

    reset_container()
    await engine.dispose()


def _default_plans() -> list[billing_models.BillingPlan]:
    starter = billing_models.BillingPlan(
        code="starter",
        name="Starter",
        interval="monthly",
        interval_count=1,
        price_cents=0,
        currency="USD",
        seat_included=1,
        feature_toggles={"export_transcripts": True},
    )
    return [starter]
