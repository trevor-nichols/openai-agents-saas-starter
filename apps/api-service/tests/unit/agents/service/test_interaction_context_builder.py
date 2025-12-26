from __future__ import annotations

from types import SimpleNamespace
from typing import Literal, cast

import pytest

from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.vector_store_overrides import VectorStoreOverrideError
from app.services.vector_stores.service import VectorStoreNotFoundError, VectorStoreService


class _FakeStore:
    def __init__(self, *, id: str, openai_id: str, tenant_id: str, name: str | None = None):
        self.id = id
        self.openai_id = openai_id
        self.tenant_id = tenant_id
        self.name = name
        self.deleted_at = None


class _FakeVectorStoreService:
    def __init__(self, stores: list[_FakeStore] | None = None, auto_store: _FakeStore | None = None):
        self.stores = stores or []
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
        return None


def _builder(
    stores: list[_FakeStore] | None,
    auto_store: _FakeStore | None,
    *,
    auto_create: bool,
    binding_mode: Literal["tenant_default", "static", "required"] = "tenant_default",
):
    settings = cast(
        Settings, SimpleNamespace(auto_create_vector_store_for_file_search=auto_create)
    )
    service = cast(VectorStoreService, _FakeVectorStoreService(stores=stores, auto_store=auto_store))
    builder = InteractionContextBuilder(
        vector_store_service=service, settings_factory=lambda: settings
    )
    spec = AgentSpec(
        key="fs_agent",
        display_name="File Searcher",
        description="",
        instructions="",
        tool_keys=("file_search",),
        vector_store_binding=binding_mode,
    )
    builder._spec_index = {spec.key: spec}
    return builder


def _actor():
    return SimpleNamespace(tenant_id="t1", user_id="u1")


@pytest.mark.asyncio
async def test_override_valid_openai_id():
    store = _FakeStore(id="db-1", openai_id="vs_ctx", tenant_id="t1")
    builder = _builder([store], None, auto_create=True)
    request = SimpleNamespace(context={"vector_store_ids": ["vs_ctx"]}, share_location=False, location=None)

    resolved = await builder._resolve_file_search_for_agents(
        agent_keys=["fs_agent"], actor=_actor(), request=request
    )

    assert resolved == {"fs_agent": {"vector_store_ids": ["vs_ctx"], "options": {}}}


@pytest.mark.asyncio
async def test_override_invalid_raises():
    builder = _builder([], None, auto_create=True)
    request = SimpleNamespace(context={"vector_store_ids": ["missing"]}, share_location=False, location=None)

    with pytest.raises(VectorStoreNotFoundError):
        await builder._resolve_file_search_for_agents(
            agent_keys=["fs_agent"], actor=_actor(), request=request
        )


@pytest.mark.asyncio
async def test_required_without_auto_create_fails_when_missing():
    builder = _builder([], None, auto_create=False, binding_mode="required")
    request = SimpleNamespace(context=None, share_location=False, location=None)

    with pytest.raises(VectorStoreNotFoundError):
        await builder._resolve_file_search_for_agents(
            agent_keys=["fs_agent"], actor=_actor(), request=request
        )


@pytest.mark.asyncio
async def test_required_raises_even_when_auto_create_enabled():
    builder = _builder([], None, auto_create=True, binding_mode="required")
    request = SimpleNamespace(context=None, share_location=False, location=None)

    with pytest.raises(VectorStoreNotFoundError):
        await builder._resolve_file_search_for_agents(
            agent_keys=["fs_agent"], actor=_actor(), request=request
        )


@pytest.mark.asyncio
async def test_primary_resolved_when_auto_create_disabled():
    primary = _FakeStore(id="db-2", openai_id="vs_primary", tenant_id="t1", name="primary")
    builder = _builder([primary], None, auto_create=False)
    request = SimpleNamespace(context=None, share_location=False, location=None)

    resolved = await builder._resolve_file_search_for_agents(
        agent_keys=["fs_agent"], actor=_actor(), request=request
    )

    assert resolved == {"fs_agent": {"vector_store_ids": ["vs_primary"], "options": {}}}


@pytest.mark.asyncio
async def test_file_search_only_resolves_requested_agents():
    store = _FakeStore(id="db-3", openai_id="vs_multi", tenant_id="t1")
    builder = _builder([store], store, auto_create=True)

    spec_extra = AgentSpec(
        key="fs_agent_two",
        display_name="File Search Two",
        description="",
        instructions="",
        tool_keys=("file_search",),
    )
    builder._spec_index[spec_extra.key] = spec_extra

    request = SimpleNamespace(context=None, share_location=False, location=None)

    resolved = await builder._resolve_file_search_for_agents(
        agent_keys=builder._file_search_agent_keys(["fs_agent"]),
        actor=_actor(),
        request=request,
    )

    assert set(resolved.keys()) == {"fs_agent"}
    assert resolved["fs_agent"]["vector_store_ids"] == ["vs_multi"]


@pytest.mark.asyncio
async def test_file_search_resolves_agent_tool_dependencies():
    store = _FakeStore(id="db-4", openai_id="vs_dep", tenant_id="t1")
    builder = _builder([store], store, auto_create=True)

    dep = AgentSpec(
        key="fs_dep",
        display_name="FS Dep",
        description="",
        instructions="",
        tool_keys=("file_search",),
    )
    builder._spec_index[dep.key] = dep
    # rebuild fs_agent spec with dependency (dataclass is frozen)
    root = builder._spec_index["fs_agent"]
    builder._spec_index[root.key] = AgentSpec(
        key=root.key,
        display_name=root.display_name,
        description=root.description,
        instructions=root.instructions,
        tool_keys=root.tool_keys,
        agent_tool_keys=("fs_dep",),
    )

    request = SimpleNamespace(context=None, share_location=False, location=None)

    resolved = await builder._resolve_file_search_for_agents(
        agent_keys=builder._file_search_agent_keys(["fs_agent"]),
        actor=_actor(),
        request=request,
    )

    assert set(resolved.keys()) == {"fs_agent", "fs_dep"}
    assert resolved["fs_dep"]["vector_store_ids"] == ["vs_dep"]


@pytest.mark.asyncio
async def test_per_agent_vector_store_override_takes_precedence():
    ctx_store = _FakeStore(id="db-5", openai_id="vs_ctx", tenant_id="t1")
    override_store = _FakeStore(id="db-6", openai_id="vs_override", tenant_id="t1")
    builder = _builder([ctx_store, override_store], override_store, auto_create=True)
    request = SimpleNamespace(
        context={"vector_store_id": "vs_ctx"},
        vector_store_overrides={"fs_agent": {"vector_store_id": "vs_override"}},
        share_location=False,
        location=None,
    )

    overrides = await builder._resolve_vector_store_overrides(
        agent_keys=["fs_agent"], actor=_actor(), request=request
    )
    resolved = await builder._resolve_file_search_for_agents(
        agent_keys=["fs_agent"],
        actor=_actor(),
        request=request,
        overrides=overrides,
    )

    assert resolved["fs_agent"]["vector_store_ids"] == ["vs_override"]


@pytest.mark.asyncio
async def test_vector_store_override_rejects_unknown_agent():
    store = _FakeStore(id="db-7", openai_id="vs_ctx", tenant_id="t1")
    builder = _builder([store], store, auto_create=True)
    request = SimpleNamespace(
        vector_store_overrides={"missing_agent": {"vector_store_id": "vs_ctx"}},
        share_location=False,
        location=None,
    )

    with pytest.raises(VectorStoreOverrideError):
        await builder._resolve_vector_store_overrides(
            agent_keys=["fs_agent"], actor=_actor(), request=request
        )


@pytest.mark.asyncio
async def test_vector_store_override_requires_file_search():
    store = _FakeStore(id="db-8", openai_id="vs_ctx", tenant_id="t1")
    builder = _builder([store], store, auto_create=True)
    builder._spec_index["fs_agent"] = AgentSpec(
        key="fs_agent",
        display_name="No FS",
        description="",
        instructions="",
        tool_keys=(),
    )
    request = SimpleNamespace(
        vector_store_overrides={"fs_agent": {"vector_store_id": "vs_ctx"}},
        share_location=False,
        location=None,
    )

    with pytest.raises(VectorStoreOverrideError):
        await builder._resolve_vector_store_overrides(
            agent_keys=["fs_agent"], actor=_actor(), request=request
        )
