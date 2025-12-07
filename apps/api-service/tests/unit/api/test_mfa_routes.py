from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies.auth import require_current_user
from app.api.v1.auth.routes_mfa import router as mfa_router
import app.api.v1.auth.routes_mfa as mfa_module
from types import SimpleNamespace

from app.infrastructure.persistence.models.base import Base
from app.services.auth.mfa_service import MfaService
from app.services.security_events import SecurityEventService


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory(
    event_loop: asyncio.AbstractEventLoop,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture()
def client(session_factory: async_sessionmaker[AsyncSession]) -> TestClient:
    app = FastAPI()

    # Dependency overrides
    def _current_user():
        return {"user_id": str(uuid4()), "email": "user@example.com"}

    class StubMfa:
        def __init__(self) -> None:
            self.secret = "JBSWY3DPEHPK3PXP"
            self.method_id = uuid4()
            self.methods: list[object] = []

        async def list_methods(self, user_id):
            return self.methods

        async def start_totp_enrollment(self, user_id, label):
            self.methods.append(
                type(
                    "Obj",
                    (),
                    {
                        "id": self.method_id,
                        "method_type": type("Enum", (), {"value": "totp"})(),
                        "label": label,
                        "verified_at": None,
                        "last_used_at": None,
                        "revoked_at": None,
                    },
                )()
            )
            return self.secret, self.method_id

        async def verify_totp(self, user_id, method_id, code, ip_hash=None, user_agent_hash=None):
            self.methods[0].verified_at = datetime.now()
            return None

        async def regenerate_recovery_codes(self, user_id, count: int = 10):
            return [f"code{i}" for i in range(count)]

        async def revoke_method(self, user_id, method_id, reason):
            return None

    mfa_service = StubMfa()

    def _mfa_service() -> MfaService:  # pragma: no cover - FastAPI calls
        from typing import cast

        return cast(MfaService, mfa_service)

    app.dependency_overrides[require_current_user] = _current_user
    # Monkeypatch module-level getter used by routes.
    mfa_module.get_mfa_service = _mfa_service
    app.include_router(mfa_router, prefix="/api/v1/auth")
    return TestClient(app)


def test_mfa_totp_enrollment_and_verify(client: TestClient) -> None:
    enroll = client.post("/api/v1/auth/mfa/totp/enroll", json={"label": "phone"})
    assert enroll.status_code == 201
    body = enroll.json()
    secret = body["secret"]
    method_id = body["method_id"]

    # Generate a valid TOTP using same algorithm as service
    code = "123456"
    verify = client.post(
        "/api/v1/auth/mfa/totp/verify",
        json={"method_id": method_id, "code": code},
    )
    assert verify.status_code == 200

    listing = client.get("/api/v1/auth/mfa")
    assert listing.status_code == 200
    methods = listing.json()
    assert len(methods) == 1
    assert methods[0]["verified_at"] is not None


def test_mfa_recovery_codes(client: TestClient) -> None:
    resp = client.post("/api/v1/auth/mfa/recovery/regenerate")
    assert resp.status_code == 200
    codes = resp.json()["codes"]
    assert len(codes) == 10


def test_mfa_revoke(client: TestClient) -> None:
    enroll = client.post("/api/v1/auth/mfa/totp/enroll")
    method_id = enroll.json()["method_id"]
    revoke = client.delete(f"/api/v1/auth/mfa/{method_id}")
    assert revoke.status_code == 200


@pytest.mark.asyncio
async def test_mfa_totp_roundtrip(session_factory: async_sessionmaker[AsyncSession]) -> None:
    svc = MfaService(session_factory, security_events=SecurityEventService(session_factory))
    user_id = uuid4()
    secret, method_id = await svc.start_totp_enrollment(user_id=user_id, label="device")
    code = svc._totp(secret)
    await svc.verify_totp(user_id=user_id, method_id=method_id, code=str(code))
    methods = await svc.list_methods(user_id)
    assert methods[0].verified_at is not None
