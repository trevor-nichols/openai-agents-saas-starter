from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import Settings
from app.domain.billing import PlanFeature, BillingPlan, TenantSubscription
from app.infrastructure.persistence.conversations.models import TenantAccount
from app.infrastructure.persistence.vector_stores.models import AgentVectorStore, VectorStore, VectorStoreFile
from app.services.vector_stores import (
    VectorLimitResolver,
    VectorStoreFileConflictError,
    VectorStoreNameConflictError,
    VectorStoreQuotaError,
    VectorStoreService,
    VectorStoreValidationError,
)
from tests.utils.sqlalchemy import create_tables


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            create_tables,
            (TenantAccount.__table__, VectorStore.__table__, VectorStoreFile.__table__, AgentVectorStore.__table__),
        )
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        vector_max_file_mb=10,
        vector_max_files_per_store=1,
        vector_max_stores_per_tenant=2,
        vector_max_total_bytes=20_000_000,
    )


@dataclass
class _FakeFile:
    id: str
    filename: str = "file.txt"
    mime_type: str = "text/plain"
    bytes: int = 1024
    usage_bytes: int = 1024
    status: str = "completed"
    last_error: str | None = None


class _FakeFilesClient:
    def __init__(self, file_meta: _FakeFile):
        self._file_meta = file_meta

    async def retrieve(self, file_id: str) -> _FakeFile:
        return self._file_meta

    async def delete(self, *, vector_store_id: str, file_id: str):
        return None


class _FakeVectorStoreFiles:
    def __init__(self, remote_file: _FakeFile):
        self._remote_file = remote_file

    async def create_and_poll(self, **kwargs):
        return self._remote_file

    async def create(self, **kwargs):
        return self._remote_file

    async def delete(self, *, vector_store_id: str, file_id: str):
        return None


class _FakeVectorStores:
    def __init__(self, remote_store, remote_file: _FakeFile):
        self._remote_store = remote_store
        self._counter = 0
        self.files = _FakeVectorStoreFiles(remote_file)

    async def create(self, **kwargs):
        self._counter += 1
        return type(
            "RemoteStore",
            (),
            {
                "id": f"vs_{self._counter}",
                "usage_bytes": getattr(self._remote_store, "usage_bytes", 0),
                "status": getattr(self._remote_store, "status", "ready"),
            },
        )

    async def delete(self, vector_store_id: str):
        return None

    async def search(self, **kwargs):
        return {"data": []}


class _FakeOpenAI:
    def __init__(self, remote_store, file_meta: _FakeFile):
        self.vector_stores = _FakeVectorStores(remote_store, file_meta)
        self.files = _FakeFilesClient(file_meta)


class _FakeBilling:
    def __init__(self, plan: BillingPlan, subscription: TenantSubscription | None = None):
        self.plan = plan
        self.subscription = subscription

    async def get_subscription(self, tenant_id: str):
        return self.subscription

    async def get_plan(self, plan_code: str):
        return self.plan


def _service(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    file_meta: _FakeFile,
    *,
    limit_resolver: VectorLimitResolver | None = None,
):
    remote_store = type("RemoteStore", (), {"id": "vs_123", "usage_bytes": 0, "status": "ready"})
    fake_client = _FakeOpenAI(remote_store, file_meta)

    return VectorStoreService(
        session_factory,
        lambda: settings,
        client_factory=lambda _tenant_id: cast(AsyncOpenAI, fake_client),
        limit_resolver=limit_resolver,
    )


@pytest.mark.asyncio
async def test_create_store_name_conflict(session_factory, settings):
    svc = _service(session_factory, settings, _FakeFile("file1"))
    tenant_id = uuid4()

    first = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")
    assert first.name == "primary"

    with pytest.raises(VectorStoreNameConflictError):
        await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")


@pytest.mark.asyncio
async def test_attach_file_mime_validation(session_factory, settings):
    bad_meta = _FakeFile("file2", mime_type="application/pdf")
    settings.vector_allowed_mime_types = ["text/plain"]
    svc = _service(session_factory, settings, bad_meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    with pytest.raises(VectorStoreValidationError):
        await svc.attach_file(
            vector_store_id=store.id,
            tenant_id=tenant_id,
            file_id="file2",
            attributes=None,
            chunking_strategy=None,
        )


@pytest.mark.asyncio
async def test_attach_file_quota_files_per_store(session_factory, settings):
    settings.vector_max_files_per_store = 1
    meta = _FakeFile("file3")
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    await svc.attach_file(
        vector_store_id=store.id,
        tenant_id=tenant_id,
        file_id="file3",
        attributes=None,
        chunking_strategy=None,
    )

    with pytest.raises(VectorStoreQuotaError):
        await svc.attach_file(
            vector_store_id=store.id,
            tenant_id=tenant_id,
            file_id="file4",
            attributes=None,
            chunking_strategy=None,
        )


@pytest.mark.asyncio
async def test_attach_file_duplicate_conflict(session_factory, settings):
    settings.vector_max_files_per_store = 5  # avoid quota interference
    meta = _FakeFile("file-dup")
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    first = await svc.attach_file(
        vector_store_id=store.id,
        tenant_id=tenant_id,
        file_id="file-dup",
        attributes=None,
        chunking_strategy=None,
    )
    assert first.openai_file_id == "file-dup"

    with pytest.raises(VectorStoreFileConflictError):
        await svc.attach_file(
            vector_store_id=store.id,
            tenant_id=tenant_id,
            file_id="file-dup",
            attributes=None,
            chunking_strategy=None,
        )


@pytest.mark.asyncio
async def test_limits_overridden_by_plan(session_factory, settings):
    settings.enable_billing = True
    # plan allows only 1 file per store and max file size 512 bytes
    plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="month",
        interval_count=1,
        price_cents=0,
        currency="usd",
        features=[
            PlanFeature(key="vector.files_per_store", display_name="files", hard_limit=1),
            PlanFeature(key="vector.max_file_bytes", display_name="file_bytes", hard_limit=512),
        ],
    )
    subscription = TenantSubscription(
        tenant_id="tenant1",
        plan_code="starter",
        status="active",
        auto_renew=True,
        billing_email=None,
        starts_at=datetime.now(),
    )
    resolver = VectorLimitResolver(
        billing_service=_FakeBilling(plan, subscription),
        settings_factory=lambda: settings,
    )
    meta = _FakeFile("file5", bytes=600)
    svc = _service(session_factory, settings, meta, limit_resolver=resolver)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    with pytest.raises(VectorStoreValidationError):
        await svc.attach_file(
            vector_store_id=store.id,
            tenant_id=tenant_id,
            file_id="file5",
            attributes=None,
            chunking_strategy=None,
        )


@pytest.mark.asyncio
async def test_delete_file_frees_usage(session_factory, settings):
    settings.vector_max_files_per_store = 5
    meta = _FakeFile("file7", usage_bytes=500)
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    await svc.attach_file(
        vector_store_id=store.id,
        tenant_id=tenant_id,
        file_id="file7",
        attributes=None,
        chunking_strategy=None,
    )
    await svc.attach_file(
        vector_store_id=store.id,
        tenant_id=tenant_id,
        file_id="file8",
        attributes=None,
        chunking_strategy=None,
    )

    async with session_factory() as session:
        refreshed = await session.get(VectorStore, store.id)
        assert refreshed.usage_bytes == 1000

    await svc.delete_file(vector_store_id=store.id, tenant_id=tenant_id, file_id="file7")

    async with session_factory() as session:
        refreshed = await session.get(VectorStore, store.id)
        assert refreshed.usage_bytes == 500

    # deleting again should be idempotent (no double decrement)
    await svc.delete_file(vector_store_id=store.id, tenant_id=tenant_id, file_id="file7")
    async with session_factory() as session:
        refreshed = await session.get(VectorStore, store.id)
        assert refreshed.usage_bytes == 500


@pytest.mark.asyncio
async def test_bind_and_unbind_agent_store(session_factory, settings):
    settings.vector_max_files_per_store = 5
    meta = _FakeFile("file-bind")
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    binding = await svc.bind_agent_to_store(
        tenant_id=tenant_id, agent_key="fs_agent", vector_store_id=store.id
    )
    assert binding.agent_key == "fs_agent"
    assert binding.vector_store_id == store.id

    # idempotent
    again = await svc.bind_agent_to_store(
        tenant_id=tenant_id, agent_key="fs_agent", vector_store_id=store.id
    )
    assert again.vector_store_id == store.id

    fetched = await svc.get_agent_binding(tenant_id=tenant_id, agent_key="fs_agent")
    assert fetched is not None
    assert fetched.vector_store_id == store.id

    await svc.unbind_agent_from_store(
        tenant_id=tenant_id, agent_key="fs_agent", vector_store_id=store.id
    )
    assert await svc.get_agent_binding(tenant_id=tenant_id, agent_key="fs_agent") is None


@pytest.mark.asyncio
async def test_bind_agent_replaces_existing(session_factory, settings):
    settings.vector_max_files_per_store = 5
    meta = _FakeFile("file-bind")
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    first = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")
    second = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="secondary")

    await svc.bind_agent_to_store(tenant_id=tenant_id, agent_key="fs_agent", vector_store_id=first.id)
    await svc.bind_agent_to_store(tenant_id=tenant_id, agent_key="fs_agent", vector_store_id=second.id)

    # Should point to the latest store
    binding = await svc.get_agent_binding(tenant_id=tenant_id, agent_key="fs_agent")
    assert binding is not None
    assert binding.vector_store_id == second.id

    # Ensure only one row exists
    async with session_factory() as session:
        count = await session.scalar(
            select(func.count()).select_from(AgentVectorStore).where(AgentVectorStore.agent_key == "fs_agent")
        )
        assert int(count or 0) == 1


@pytest.mark.asyncio
async def test_get_store_by_openai_id(session_factory, settings):
    meta = _FakeFile("file-meta")
    svc = _service(session_factory, settings, meta)
    tenant_id = uuid4()
    store = await svc.create_store(tenant_id=tenant_id, owner_user_id=None, name="primary")

    fetched = await svc.get_store_by_openai_id(tenant_id=tenant_id, openai_id=store.openai_id)
    assert fetched is not None
    assert fetched.id == store.id
