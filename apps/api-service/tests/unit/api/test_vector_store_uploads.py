from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import importlib

vector_router_module = importlib.import_module("app.api.v1.vector_stores.router")
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context
from app.api.v1.vector_stores.router import _svc as vector_store_svc
from app.api.v1.vector_stores.router import router as vector_stores_router
from app.core.security import get_current_user


class StubVectorStoreService:
    def __init__(self, file_obj: SimpleNamespace) -> None:
        self._file = file_obj
        self.last_attach_kwargs: dict[str, object] | None = None

    async def attach_storage_object(
        self,
        *,
        vector_store_id: uuid.UUID,
        tenant_id: uuid.UUID,
        object_id: uuid.UUID,
        attributes: dict[str, object] | None,
        chunking_strategy: dict[str, object] | None,
        poll: bool,
    ):
        self.last_attach_kwargs = {
            "vector_store_id": vector_store_id,
            "tenant_id": tenant_id,
            "object_id": object_id,
            "attributes": attributes,
            "chunking_strategy": chunking_strategy,
            "poll": poll,
        }
        return self._file


class AccessSpy:
    calls: list[dict[str, object]] = []

    def __init__(self, *, vector_store_service, settings_factory=None) -> None:
        self._vector_store_service = vector_store_service
        self._settings_factory = settings_factory

    async def assert_agent_can_attach(self, **kwargs) -> None:
        self.__class__.calls.append(kwargs)


def _fake_file() -> SimpleNamespace:
    now = datetime.now(tz=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        openai_file_id="file_123",
        vector_store_id=uuid.uuid4(),
        filename="example.txt",
        mime_type="text/plain",
        size_bytes=128,
        usage_bytes=128,
        status="completed",
        attributes_json={},
        chunking_json=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )


def _build_client(service: StubVectorStoreService, tenant_id: uuid.UUID) -> TestClient:
    app = FastAPI()
    app.dependency_overrides[vector_store_svc] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "user-1",
        "payload": {"email_verified": True},
        "email_verified": True,
    }
    app.dependency_overrides[get_tenant_context] = lambda: TenantContext(
        tenant_id=str(tenant_id),
        role=TenantRole.OWNER,
        user={"user_id": "user-1"},
    )
    app.include_router(vector_stores_router, prefix="/api/v1")
    return TestClient(app)


def test_vector_store_upload_without_agent_key_skips_agent_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    AccessSpy.calls = []
    monkeypatch.setattr(vector_router_module, "AgentVectorStoreAccessService", AccessSpy)

    tenant_id = uuid.uuid4()
    service = StubVectorStoreService(_fake_file())
    client = _build_client(service, tenant_id)
    vector_store_id = uuid.uuid4()
    object_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/vector-stores/{vector_store_id}/files/upload",
        json={"object_id": str(object_id)},
    )

    assert response.status_code == 201
    assert AccessSpy.calls == []
    assert service.last_attach_kwargs is not None
    assert service.last_attach_kwargs["object_id"] == object_id
    assert service.last_attach_kwargs["vector_store_id"] == vector_store_id


def test_vector_store_upload_with_agent_key_enforces_agent_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    AccessSpy.calls = []
    monkeypatch.setattr(vector_router_module, "AgentVectorStoreAccessService", AccessSpy)

    tenant_id = uuid.uuid4()
    service = StubVectorStoreService(_fake_file())
    client = _build_client(service, tenant_id)
    vector_store_id = uuid.uuid4()
    object_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/vector-stores/{vector_store_id}/files/upload",
        json={"object_id": str(object_id), "agent_key": "fs_agent"},
    )

    assert response.status_code == 201
    assert len(AccessSpy.calls) == 1
    assert AccessSpy.calls[0]["agent_key"] == "fs_agent"
    assert AccessSpy.calls[0]["tenant_id"] == str(tenant_id)
    assert service.last_attach_kwargs is not None
    assert service.last_attach_kwargs["object_id"] == object_id
