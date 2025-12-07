from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies.auth import require_current_user
from app.api.dependencies.tenant import TenantContext, TenantRole
from app.api.v1.users.routes_notifications import router as notifications_router
import app.api.v1.users.routes_notifications as notifications_module
from app.infrastructure.persistence.models.base import Base
from app.services.notification_preferences import NotificationPreferenceService


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture()
def client(session_factory: async_sessionmaker[AsyncSession]) -> TestClient:
    app = FastAPI()

    def _current_user():
        return {"user_id": str(uuid4())}

    def _tenant_context():
        return TenantContext(tenant_id=str(uuid4()), role=TenantRole.VIEWER, user={"user_id": str(uuid4())})

    class StubPrefService:
        def __init__(self) -> None:
            self.items: list[object] = []

        async def upsert_preference(self, **kwargs):
            obj = type(
                "Obj",
                (),
                {
                    "id": uuid4(),
                    "channel": kwargs["channel"],
                    "category": kwargs["category"],
                    "enabled": kwargs["enabled"],
                    "tenant_id": kwargs.get("tenant_id"),
                },
            )()
            self.items = [obj]
            return obj

        async def list_preferences(self, **kwargs):
            return self.items

    svc = StubPrefService()

    def _svc() -> NotificationPreferenceService:  # pragma: no cover
        from typing import cast

        return cast(NotificationPreferenceService, svc)

    app.dependency_overrides[require_current_user] = _current_user
    dep = notifications_router.routes[0].dependant.dependencies[1].call  # type: ignore[attr-defined]
    app.dependency_overrides[dep] = _tenant_context
    app.dependency_overrides[notifications_module._service] = _svc
    notifications_module.get_notification_preference_service = _svc
    app.include_router(notifications_router, prefix="/api/v1")
    return TestClient(app)


def test_upsert_and_list_notification_preferences(client: TestClient) -> None:
    payload = {
        "channel": "email",
        "category": "alerts",
        "enabled": False,
        "tenant_id": None,
    }
    headers = {"X-Tenant-Id": str(uuid4())}
    resp = client.put("/api/v1/users/notification-preferences", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["channel"] == "email"
    assert body["enabled"] is False

    listing = client.get("/api/v1/users/notification-preferences", headers=headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["category"] == "alerts"
