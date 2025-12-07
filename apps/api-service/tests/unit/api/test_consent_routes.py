from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies.auth import require_current_user
from app.api.v1.users.routes_consents import router as consents_router
import app.api.v1.users.routes_consents as consents_module
from app.infrastructure.persistence.models.base import Base
from app.services.consent_service import ConsentService


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

    class StubConsentService:
        def __init__(self) -> None:
            self.rows: list[object] = []

        async def record(self, **kwargs):
            self.rows.append(
                type(
                    "Obj",
                    (),
                    {
                        "policy_key": kwargs["policy_key"],
                        "version": kwargs["version"],
                        "accepted_at": kwargs.get("accepted_at") or datetime.now(),
                    },
                )(),
            )

        async def list_for_user(self, user_id, limit: int = 50):
            return self.rows

    consent_service = StubConsentService()

    def _consent_service() -> ConsentService:  # pragma: no cover - injected
        from typing import cast

        return cast(ConsentService, consent_service)

    app.dependency_overrides[require_current_user] = _current_user
    consents_module.get_consent_service = _consent_service
    app.include_router(consents_router, prefix="/api/v1")
    return TestClient(app)


def test_record_and_list_consents(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/users/consents",
        json={"policy_key": "tos", "version": "v1", "ip_hash": "h", "user_agent_hash": "ua"},
    )
    assert resp.status_code == status.HTTP_201_CREATED

    listing = client.get("/api/v1/users/consents")
    assert listing.status_code == 200
    body = listing.json()
    assert len(body) == 1
    assert body[0]["policy_key"] == "tos"
