"""Integration smoke tests for Postgres migrations and repositories."""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.domain.billing import TenantSubscription
from app.domain.conversations import ConversationMetadata, ConversationMessage
from app.infrastructure.persistence.billing.postgres import PostgresBillingRepository
from app.infrastructure.persistence.conversations.models import SubscriptionUsage as ORMSubscriptionUsage
from app.infrastructure.persistence.conversations.postgres import (
    PostgresConversationRepository,
)

pytestmark = pytest.mark.postgres

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def _require_database_url() -> URL:
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        pytest.skip("DATABASE_URL not set; skipping Postgres integration tests.")
    return make_url(raw_url)


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    """Ensure a session-scoped event loop for async fixtures."""

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
    """Provision a temporary Postgres database and tear it down afterwards."""

    base_url = _require_database_url()
    temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
    admin_url = base_url.set(drivername="postgresql", database="postgres")

    conn = await asyncpg.connect(str(admin_url))
    try:
        await conn.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        await conn.close()

    test_url = base_url.set(database=temp_db_name)
    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        # Terminate lingering connections and drop the temp database.
        admin_conn = await asyncpg.connect(str(admin_url))
        try:
            await admin_conn.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1 AND pid <> pg_backend_pid()
                """,
                temp_db_name,
            )
            await admin_conn.execute(f'DROP DATABASE "{temp_db_name}"')
        finally:
            await admin_conn.close()


@pytest.fixture(scope="session")
async def migrated_engine(postgres_database: str) -> AsyncIterator[AsyncEngine]:
    """Apply alembic migrations against the temporary database and yield an engine."""

    alembic_cfg = Config(str(ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_database)

    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    engine = create_async_engine(postgres_database, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()
        await asyncio.to_thread(command.downgrade, alembic_cfg, "base")


@pytest.fixture(scope="session")
def migrated_session_factory(migrated_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(migrated_engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_core_tables_exist(migrated_engine: AsyncEngine) -> None:
    """Ensure key tables exist after migrations are applied."""

    expected_tables = {
        "tenant_accounts",
        "agent_conversations",
        "agent_messages",
        "billing_plans",
        "tenant_subscriptions",
    }

    async with migrated_engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
        )
        tables = {row[0] for row in result.fetchall()}

    missing = expected_tables.difference(tables)
    assert not missing, f"Missing expected tables: {missing}"


@pytest.mark.asyncio
async def test_repository_roundtrip(migrated_engine: AsyncEngine) -> None:
    """Verify the Postgres conversation repository can persist and read messages."""

    session_factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    repository = PostgresConversationRepository(session_factory)

    conversation_id = str(uuid.uuid4())

    await repository.add_message(
        conversation_id,
        ConversationMessage(role="user", content="Hello durable world!"),
        metadata=ConversationMetadata(agent_entrypoint="triage"),
    )
    await repository.add_message(
        conversation_id,
        ConversationMessage(role="assistant", content="Persistence acknowledged."),
        metadata=ConversationMetadata(
            agent_entrypoint="triage",
            active_agent="triage",
            total_tokens_prompt=10,
            total_tokens_completion=12,
        ),
    )

    messages = await repository.get_messages(conversation_id)
    assert len(messages) == 2
    assert messages[0].content == "Hello durable world!"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_repository_preserves_custom_conversation_id(
    migrated_engine: AsyncEngine,
) -> None:
    """Ensure custom caller-supplied IDs remain intact in listings and lookups."""

    session_factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    repository = PostgresConversationRepository(session_factory)

    conversation_id = "integration-test-thread"

    await repository.add_message(
        conversation_id,
        ConversationMessage(role="user", content="Hello hashed world!"),
        metadata=ConversationMetadata(agent_entrypoint="triage"),
    )

    ids = await repository.list_conversation_ids()
    assert conversation_id in ids

    records = await repository.iter_conversations()
    assert any(record.conversation_id == conversation_id for record in records)

    await repository.clear_conversation(conversation_id)
    ids_after = await repository.list_conversation_ids()
    assert conversation_id not in ids_after


@pytest.mark.asyncio
async def test_billing_repository_reads_seeded_plans(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repository = PostgresBillingRepository(migrated_session_factory)
    plans = await repository.list_plans()

    codes = {plan.code for plan in plans}
    assert {"starter", "pro"}.issubset(codes)

    subscription = await repository.get_subscription("nonexistent-tenant")
    assert subscription is None


@pytest.mark.asyncio
async def test_billing_subscription_upsert_roundtrip(
    migrated_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repository = PostgresBillingRepository(migrated_session_factory)
    plan = (await repository.list_plans())[0]

    tenant_id = str(uuid.uuid4())
    subscription = TenantSubscription(
        tenant_id=tenant_id,
        plan_code=plan.code,
        status="active",
        auto_renew=True,
        billing_email="owner@example.com",
        starts_at=datetime.now(timezone.utc),
        seat_count=plan.seat_included,
        metadata={"source": "integration-test"},
        processor="stripe",
        processor_customer_id="cus_test",
        processor_subscription_id="sub_test",
    )

    await repository.upsert_subscription(subscription)

    stored = await repository.get_subscription(tenant_id)
    assert stored is not None
    assert stored.plan_code == plan.code
    assert stored.processor_subscription_id == "sub_test"

    updated = await repository.update_subscription(
        tenant_id,
        auto_renew=False,
        billing_email="billing@example.com",
        seat_count=7,
    )

    assert updated.auto_renew is False
    assert updated.billing_email == "billing@example.com"
    assert updated.seat_count == 7

    now = datetime.now(timezone.utc)
    await repository.record_usage(
        tenant_id,
        feature_key="messages",
        quantity=10,
        period_start=now,
        period_end=now,
        idempotency_key="usage-key",
    )
    # duplicate should be ignored
    await repository.record_usage(
        tenant_id,
        feature_key="messages",
        quantity=10,
        period_start=now,
        period_end=now,
        idempotency_key="usage-key",
    )

    async with migrated_session_factory() as session:
        result = await session.execute(
            select(ORMSubscriptionUsage).where(
                ORMSubscriptionUsage.external_event_id == "usage-key"
            )
        )
        usage_rows = result.scalars().all()
        assert len(usage_rows) == 1
        assert usage_rows[0].quantity == 10
