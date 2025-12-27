from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.dependencies.auth import require_current_user
from app.api.v1.users import routes_profile
from app.domain.users import (
    UserEmailChangeResult,
    UserProfilePatch,
    UserProfileSummary,
    UserRecord,
    UserStatus,
)


class _StubAuthService:
    def __init__(self, revoked: int = 0) -> None:
        self.revoked = revoked
        self.calls: list[tuple[str, str]] = []

    async def revoke_user_sessions(self, user_id: UUID, *, reason: str = "") -> int:
        self.calls.append((str(user_id), reason))
        return self.revoked


class _StubEmailService:
    def __init__(self, sent: bool) -> None:
        self.sent = sent
        self.calls: list[tuple[str, str]] = []

    async def send_verification_email(
        self,
        *,
        user_id: str,
        email: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> bool:
        self.calls.append((user_id, email or ""))
        return self.sent


class _StubSecurityEventService:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    async def record(self, **kwargs: object) -> None:
        self.events.append(dict(kwargs))


class _StubUserService:
    def __init__(self, profile: UserProfileSummary, record: UserRecord) -> None:
        self.profile = profile
        self.record = record
        self.profile_updates: list[dict[str, object]] = []
        self.email_changes: list[dict[str, object]] = []
        self.disabled: list[str] = []

    async def update_user_profile(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        update: UserProfilePatch,
        provided_fields: set[str],
    ) -> UserProfileSummary:
        self.profile_updates.append(
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "update": update,
                "provided_fields": set(provided_fields),
            }
        )
        for field in provided_fields:
            setattr(self.profile, field, getattr(update, field))
        return self.profile

    async def change_email(
        self,
        *,
        user_id: UUID,
        current_password: str,
        new_email: str,
    ) -> UserEmailChangeResult:
        self.email_changes.append(
            {
                "user_id": user_id,
                "current_password": current_password,
                "new_email": new_email,
            }
        )
        return UserEmailChangeResult(user=self.record, changed=True)

    async def disable_account(self, *, user_id: UUID, current_password: str) -> None:
        self.disabled.append(str(user_id))


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    user_id = uuid4()
    tenant_id = uuid4()
    profile = UserProfileSummary(
        user_id=user_id,
        tenant_id=tenant_id,
        email="user@example.com",
        display_name="User",
        given_name="Test",
        family_name="User",
        avatar_url=None,
        timezone="UTC",
        locale="en-US",
        role="admin",
        email_verified=False,
    )
    record = UserRecord(
        id=user_id,
        email="new@example.com",
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name=profile.display_name,
        given_name=profile.given_name,
        family_name=profile.family_name,
        avatar_url=profile.avatar_url,
        timezone=profile.timezone,
        locale=profile.locale,
        memberships=[],
        email_verified_at=None,
    )
    stub_user_service = _StubUserService(profile, record)
    stub_auth_service = _StubAuthService(revoked=2)
    stub_email_service = _StubEmailService(sent=True)
    stub_security_service = _StubSecurityEventService()

    def _current_user():
        return {"user_id": str(user_id), "payload": {"tenant_id": str(tenant_id)}}

    def _user_service():
        return stub_user_service

    def _email_service():
        return stub_email_service

    def _security_service():
        return stub_security_service

    monkeypatch.setattr(routes_profile, "auth_service", stub_auth_service)
    monkeypatch.setattr(routes_profile, "get_user_service", _user_service)
    monkeypatch.setattr(routes_profile, "get_email_verification_service", _email_service)
    monkeypatch.setattr(routes_profile, "get_security_event_service", _security_service)

    app = FastAPI()
    app.dependency_overrides[require_current_user] = _current_user
    app.include_router(routes_profile.router, prefix="/api/v1")
    return TestClient(app)


def test_update_profile_returns_payload(client: TestClient) -> None:
    resp = client.patch("/api/v1/users/me/profile", json={"display_name": "New Name"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["display_name"] == "New Name"
    assert body["data"]["timezone"] == "UTC"
    assert body["data"]["locale"] == "en-US"


def test_change_email_sends_verification(client: TestClient) -> None:
    resp = client.patch(
        "/api/v1/users/me/email",
        json={"current_password": "Password123!", "new_email": "new@example.com"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["email"] == "new@example.com"
    assert body["data"]["verification_sent"] is True


def test_disable_account_revokes_sessions(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/users/me/disable",
        json={"current_password": "Password123!"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["disabled"] is True
    assert body["data"]["revoked_sessions"] == 2
