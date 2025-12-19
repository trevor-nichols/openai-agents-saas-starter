from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.tenant import TenantContext, TenantRole
from app.api.v1.assets.router import _svc as assets_svc
from app.api.v1.assets.router import router as assets_router
from app.domain.assets import AssetRecord, AssetView
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid as coerce_conversation_uuid_from_persistence,
)


class StubAssetService:
    def __init__(self, view: AssetView) -> None:
        self._view = view
        self.deleted: bool = False
        self.last_kwargs: dict[str, object] | None = None

    async def list_assets(self, **kwargs):
        self.last_kwargs = kwargs
        return [self._view]

    async def get_asset(self, **kwargs):
        return self._view

    async def get_download_url(self, **kwargs):
        presign = type(
            "Presign",
            (),
            {"url": "https://example.com/asset", "method": "GET", "headers": {}},
        )
        storage_obj = type("StorageObj", (), {"id": self._view.asset.storage_object_id})
        return presign, storage_obj

    async def delete_asset(self, **kwargs) -> None:
        self.deleted = True

    async def get_thumbnail_urls(self, **kwargs):
        item = type(
            "Thumb",
            (),
            {
                "asset_id": self._view.asset.id,
                "storage_object_id": self._view.asset.storage_object_id,
                "download_url": "https://example.com/thumb",
                "method": "GET",
                "headers": {},
                "expires_in_seconds": 900,
            },
        )
        return [item], [], []

    def signed_url_ttl(self) -> int:
        return 900


def _override_auth(app: FastAPI, tenant_id: uuid.UUID) -> None:
    def _current_user():
        return {"user_id": "user-1"}

    def _tenant_context():
        return TenantContext(
            tenant_id=str(tenant_id),
            role=TenantRole.OWNER,
            user={"user_id": "user-1"},
        )

    for route in assets_router.routes:
        for dep in route.dependant.dependencies:  # type: ignore[attr-defined]
            module = getattr(dep.call, "__module__", "")
            if module.endswith("auth"):
                app.dependency_overrides[dep.call] = _current_user
            elif module.endswith("tenant"):
                app.dependency_overrides[dep.call] = _tenant_context


def _client_with_stub(view: AssetView) -> tuple[TestClient, StubAssetService]:
    app = FastAPI()
    stub = StubAssetService(view)
    app.dependency_overrides[assets_svc] = lambda: stub
    _override_auth(app, view.asset.tenant_id)
    app.include_router(assets_router, prefix="/api/v1")
    return TestClient(app), stub


def _asset_view() -> AssetView:
    tenant_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    storage_id = uuid.uuid4()
    asset = AssetRecord(
        id=asset_id,
        tenant_id=tenant_id,
        storage_object_id=storage_id,
        asset_type="image",
        source_tool="image_generation",
        conversation_id=None,
        message_id=None,
        tool_call_id="tool-1",
        response_id="resp-1",
        container_id=None,
        openai_file_id=None,
        metadata={"kind": "chart"},
    )
    return AssetView(
        asset=asset,
        filename="asset.png",
        mime_type="image/png",
        size_bytes=1024,
        agent_key="image_studio",
        storage_status="ready",
        storage_created_at=None,
    )


def test_list_assets_returns_payload() -> None:
    view = _asset_view()
    client, _ = _client_with_stub(view)

    response = client.get("/api/v1/assets")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["id"] == str(view.asset.id)
    assert body["items"][0]["asset_type"] == "image"


def test_list_assets_accepts_non_uuid_conversation_id() -> None:
    view = _asset_view()
    client, stub = _client_with_stub(view)
    conversation_id = "external-conversation-123"

    response = client.get(f"/api/v1/assets?conversation_id={conversation_id}")

    assert response.status_code == 200
    assert stub.last_kwargs is not None
    assert (
        stub.last_kwargs["conversation_id"]
        == coerce_conversation_uuid_from_persistence(conversation_id)
    )


def test_asset_download_url() -> None:
    view = _asset_view()
    client, _ = _client_with_stub(view)

    response = client.get(f"/api/v1/assets/{view.asset.id}/download-url")

    assert response.status_code == 200
    body = response.json()
    assert body["download_url"].startswith("https://example.com/")
    assert body["storage_object_id"] == str(view.asset.storage_object_id)


def test_delete_asset() -> None:
    view = _asset_view()
    client, stub = _client_with_stub(view)

    response = client.delete(f"/api/v1/assets/{view.asset.id}")

    assert response.status_code == 204
    assert stub.deleted is True


def test_asset_thumbnail_urls() -> None:
    view = _asset_view()
    client, _ = _client_with_stub(view)

    response = client.post(
        "/api/v1/assets/thumbnail-urls",
        json={"asset_ids": [str(view.asset.id)]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["asset_id"] == str(view.asset.id)
