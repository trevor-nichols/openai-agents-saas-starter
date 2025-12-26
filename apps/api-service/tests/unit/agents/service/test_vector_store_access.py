from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.services.agents.vector_store_access import AgentVectorStoreAccessError, AgentVectorStoreAccessService
from app.services.vector_stores.service import VectorStoreNotFoundError, VectorStoreService


class _FakeStore:
    def __init__(self, *, id: str, openai_id: str, tenant_id: str, name: str | None = None):
        self.id = id
        self.openai_id = openai_id
        self.tenant_id = tenant_id
        self.name = name
        self.deleted_at = None


class _FakeVectorStoreService:
    def __init__(
        self,
        *,
        stores: list[_FakeStore],
        bindings: dict[str, str] | None = None,
        auto_store: _FakeStore | None = None,
    ):
        self.stores = stores
        self.bindings = bindings or {}
        self.auto_store = auto_store

    async def get_store(self, *, vector_store_id, tenant_id):
        for store in self.stores:
            if str(store.id) == str(vector_store_id) and store.tenant_id == tenant_id:
                return store
        raise VectorStoreNotFoundError("not found")

    async def get_store_by_openai_id(self, *, tenant_id, openai_id):
        for store in self.stores:
            if store.openai_id == openai_id and store.tenant_id == tenant_id:
                return store
        return None

    async def get_store_by_name(self, *, tenant_id, name: str):
        for store in self.stores:
            if store.tenant_id == tenant_id and store.name == name:
                return store
        return None

    async def ensure_primary_store(self, *, tenant_id, owner_user_id=None):
        existing = await self.get_store_by_name(tenant_id=tenant_id, name="primary")
        if existing:
            return existing
        return self.auto_store

    async def get_agent_binding(self, *, tenant_id, agent_key):
        openai_id = self.bindings.get(agent_key)
        if not openai_id:
            return None
        return SimpleNamespace(openai_id=openai_id)


def _service(
    *,
    specs: list[AgentSpec],
    stores: list[_FakeStore],
    bindings: dict[str, str] | None = None,
    auto_store: _FakeStore | None = None,
    auto_create: bool = True,
):
    settings = cast(Settings, SimpleNamespace(auto_create_vector_store_for_file_search=auto_create))
    service = cast(
        VectorStoreService,
        _FakeVectorStoreService(stores=stores, bindings=bindings, auto_store=auto_store),
    )
    access = AgentVectorStoreAccessService(vector_store_service=service, settings_factory=lambda: settings)
    access._spec_index = {spec.key: spec for spec in specs}
    return access


@pytest.mark.asyncio
async def test_rejects_agent_without_file_search():
    spec = AgentSpec(
        key="no_fs",
        display_name="No FS",
        description="",
        instructions="",
        tool_keys=(),
    )
    store = _FakeStore(id="db-1", openai_id="vs_primary", tenant_id="t1", name="primary")
    access = _service(specs=[spec], stores=[store])

    with pytest.raises(AgentVectorStoreAccessError):
        await access.assert_agent_can_attach(
            agent_key="no_fs",
            tenant_id="t1",
            user_id="u1",
            vector_store_id="db-1",
        )


@pytest.mark.asyncio
async def test_allows_static_binding_match():
    spec = AgentSpec(
        key="fs_static",
        display_name="Static",
        description="",
        instructions="",
        tool_keys=("file_search",),
        vector_store_binding="static",
        vector_store_ids=("vs_allowed",),
    )
    store = _FakeStore(id="db-1", openai_id="vs_allowed", tenant_id="t1")
    access = _service(specs=[spec], stores=[store])

    await access.assert_agent_can_attach(
        agent_key="fs_static",
        tenant_id="t1",
        user_id="u1",
        vector_store_id="db-1",
    )


@pytest.mark.asyncio
async def test_rejects_store_not_in_binding():
    spec = AgentSpec(
        key="fs_static",
        display_name="Static",
        description="",
        instructions="",
        tool_keys=("file_search",),
        vector_store_binding="static",
        vector_store_ids=("vs_allowed",),
    )
    store = _FakeStore(id="db-1", openai_id="vs_other", tenant_id="t1")
    access = _service(specs=[spec], stores=[store])

    with pytest.raises(AgentVectorStoreAccessError):
        await access.assert_agent_can_attach(
            agent_key="fs_static",
            tenant_id="t1",
            user_id="u1",
            vector_store_id="db-1",
        )


@pytest.mark.asyncio
async def test_allows_db_binding_match():
    spec = AgentSpec(
        key="fs_bound",
        display_name="Bound",
        description="",
        instructions="",
        tool_keys=("file_search",),
    )
    store = _FakeStore(id="db-1", openai_id="vs_bound", tenant_id="t1")
    access = _service(
        specs=[spec],
        stores=[store],
        bindings={"fs_bound": "vs_bound"},
    )

    await access.assert_agent_can_attach(
        agent_key="fs_bound",
        tenant_id="t1",
        user_id="u1",
        vector_store_id="db-1",
    )


@pytest.mark.asyncio
async def test_tenant_default_requires_primary_match():
    spec = AgentSpec(
        key="fs_default",
        display_name="Default",
        description="",
        instructions="",
        tool_keys=("file_search",),
        vector_store_binding="tenant_default",
    )
    primary = _FakeStore(id="db-1", openai_id="vs_primary", tenant_id="t1", name="primary")
    other = _FakeStore(id="db-2", openai_id="vs_other", tenant_id="t1")
    access = _service(specs=[spec], stores=[primary, other])

    await access.assert_agent_can_attach(
        agent_key="fs_default",
        tenant_id="t1",
        user_id="u1",
        vector_store_id="db-1",
    )

    with pytest.raises(AgentVectorStoreAccessError):
        await access.assert_agent_can_attach(
            agent_key="fs_default",
            tenant_id="t1",
            user_id="u1",
            vector_store_id="db-2",
        )
