"""Deterministic seed orchestration for Playwright critical flows."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.container import ApplicationContainer, get_container
from app.core.settings import Settings, get_settings
from app.domain.storage import StorageProviderProtocol
from app.infrastructure.storage.registry import get_storage_provider
from app.services.test_fixtures.context import TenantSeedContext
from app.services.test_fixtures.errors import TestFixtureError
from app.services.test_fixtures.schemas import (
    FixtureApplyResult,
    FixtureTenant,
    FixtureTenantResult,
    PlaywrightFixtureSpec,
)
from app.services.test_fixtures.seeders.assets import ensure_assets
from app.services.test_fixtures.seeders.conversations import ensure_conversations
from app.services.test_fixtures.seeders.subscriptions import ensure_subscription
from app.services.test_fixtures.seeders.tenants import ensure_tenant
from app.services.test_fixtures.seeders.usage import (
    ensure_usage_counters,
    ensure_usage_records,
)
from app.services.test_fixtures.seeders.users import ensure_users


class TestFixtureService:
    """Applies deterministic fixture specifications into the persistence layer."""

    def __init__(
        self,
        container: ApplicationContainer | None = None,
        settings_provider: Callable[[], Settings] = get_settings,
        storage_provider_resolver: Callable[
            [Settings], StorageProviderProtocol
        ] = get_storage_provider,
    ) -> None:
        self._container = container or get_container()
        self._settings_provider = settings_provider
        self._storage_provider_resolver = storage_provider_resolver

    async def apply_spec(self, spec: PlaywrightFixtureSpec) -> FixtureApplyResult:
        if not spec.tenants:
            raise TestFixtureError("Fixture specification must include at least one tenant.")

        session_factory = self._container.session_factory
        if session_factory is None:
            raise TestFixtureError("Database session factory is not configured.")

        results: dict[str, FixtureTenantResult] = {}
        for tenant_spec in spec.tenants:
            context = await self._apply_tenant(session_factory, tenant_spec)
            results[tenant_spec.slug] = FixtureTenantResult(
                tenant_id=str(context.tenant.id),
                plan_code=context.plan_code,
                users=context.user_results,
                conversations=context.conversation_results,
                assets=context.asset_results,
            )

        return FixtureApplyResult(tenants=results, generated_at=datetime.now(UTC))

    async def _apply_tenant(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        tenant_spec: FixtureTenant,
    ) -> TenantSeedContext:
        async with session_factory() as session:
            async with session.begin():
                tenant = await ensure_tenant(session, tenant_spec)
                context = TenantSeedContext(
                    tenant=tenant,
                    plan_code=tenant_spec.plan_code,
                    subscription=None,
                    user_results={},
                    conversation_results={},
                    asset_results={},
                )

                if tenant_spec.plan_code:
                    context.subscription = await ensure_subscription(
                        session=session,
                        tenant=tenant,
                        plan_code=tenant_spec.plan_code,
                        billing_email=tenant_spec.billing_email
                        or (tenant_spec.users[0].email if tenant_spec.users else None),
                    )

                context.user_results = await ensure_users(
                    session=session,
                    tenant=tenant,
                    users=tenant_spec.users,
                )

                if tenant_spec.conversations:
                    context.conversation_results = await ensure_conversations(
                        session=session,
                        tenant=tenant,
                        user_results=context.user_results,
                        conversations=tenant_spec.conversations,
                    )

                if tenant_spec.usage_counters:
                    await ensure_usage_counters(
                        session=session,
                        tenant=tenant,
                        user_results=context.user_results,
                        usage_counters=tenant_spec.usage_counters,
                    )

                if tenant_spec.assets:
                    context.asset_results = await ensure_assets(
                        session=session,
                        tenant=tenant,
                        user_results=context.user_results,
                        conversation_results=context.conversation_results,
                        assets=tenant_spec.assets,
                        settings_provider=self._settings_provider,
                        storage_provider_resolver=self._storage_provider_resolver,
                    )

                if tenant_spec.usage and context.subscription is not None:
                    await ensure_usage_records(
                        session=session,
                        subscription=context.subscription,
                        usage_entries=tenant_spec.usage,
                    )

        return context


__all__ = ["TestFixtureService"]
