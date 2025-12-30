"""Contract tests for tenant team management endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_token_signer
from app.core.settings import get_settings
from app.domain.auth import UserSessionTokens
from app.domain.team import (
    TeamInvite,
    TeamInviteAcceptResult,
    TeamInviteStatus,
    TeamMember,
    TeamMemberListResult,
)
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserStatus
from app.api.v1.tenants import routes_invites, routes_members
from app.domain.team_errors import OwnerRoleAssignmentError, TeamMemberAlreadyExistsError
from app.services.team.invite_service import TeamInviteIssueResult
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as http_client:
        yield http_client


@pytest.fixture
def mock_membership_service() -> Generator[AsyncMock, None, None]:
    mock = AsyncMock()
    previous = app.dependency_overrides.get(routes_members._membership_service)
    app.dependency_overrides[routes_members._membership_service] = lambda: mock
    try:
        yield mock
    finally:
        if previous is None:
            app.dependency_overrides.pop(routes_members._membership_service, None)
        else:
            app.dependency_overrides[routes_members._membership_service] = previous


@pytest.fixture
def mock_invite_service() -> Generator[AsyncMock, None, None]:
    mock = AsyncMock()
    previous = app.dependency_overrides.get(routes_invites._invite_service)
    app.dependency_overrides[routes_invites._invite_service] = lambda: mock
    try:
        yield mock
    finally:
        if previous is None:
            app.dependency_overrides.pop(routes_invites._invite_service, None)
        else:
            app.dependency_overrides[routes_invites._invite_service] = previous


def _mint_token(*, tenant_id: str, roles: list[str], scopes: list[str]) -> str:
    signer = get_token_signer()
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": f"user:{uuid4()}",
        "token_use": "access",
        "iss": settings.app_name,
        "aud": settings.auth_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "tenant_id": tenant_id,
        "roles": roles,
        "scope": " ".join(scopes),
        "email_verified": True,
    }
    return signer.sign(payload).primary.token


def _headers(*, token: str, tenant_id: str, tenant_role: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": tenant_role,
    }


def test_list_members_returns_members(
    client: TestClient, mock_membership_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["owner"], scopes=["billing:manage"])
    member = TeamMember(
        user_id=uuid4(),
        tenant_id=UUID(tenant_id),
        email="owner@example.com",
        display_name="Owner",
        role=TenantRole.OWNER,
        status=UserStatus.ACTIVE,
        email_verified=True,
        joined_at=datetime.now(UTC),
    )
    mock_membership_service.list_members = AsyncMock(
        return_value=TeamMemberListResult(members=[member], total=1, owner_count=1)
    )

    response = client.get(
        "/api/v1/tenants/members",
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="owner"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["owner_count"] == 1
    assert body["members"][0]["email"] == member.email
    mock_membership_service.list_members.assert_awaited_once()


def test_add_member_conflict(client: TestClient, mock_membership_service: AsyncMock) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["admin"], scopes=["billing:manage"])
    mock_membership_service.add_member_by_email = AsyncMock(
        side_effect=TeamMemberAlreadyExistsError("already")
    )

    response = client.post(
        "/api/v1/tenants/members",
        json={"email": "member@example.com", "role": "member"},
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "Conflict"


def test_add_member_owner_requires_owner(
    client: TestClient, mock_membership_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["admin"], scopes=["billing:manage"])
    mock_membership_service.add_member_by_email = AsyncMock(
        side_effect=OwnerRoleAssignmentError("Only owners can assign owner.")
    )

    response = client.post(
        "/api/v1/tenants/members",
        json={"email": "owner@example.com", "role": "owner"},
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="admin"),
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error"] == "Forbidden"


def test_issue_invite_returns_token(
    client: TestClient, mock_invite_service: AsyncMock
) -> None:
    tenant_id = str(uuid4())
    token = _mint_token(tenant_id=tenant_id, roles=["owner"], scopes=["billing:manage"])
    invite = TeamInvite(
        id=uuid4(),
        tenant_id=UUID(tenant_id),
        token_hash="hash",
        token_hint="hint",
        invited_email="invitee@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.ACTIVE,
        created_by_user_id=None,
        accepted_by_user_id=None,
        accepted_at=None,
        revoked_at=None,
        revoked_reason=None,
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mock_invite_service.issue_invite = AsyncMock(
        return_value=TeamInviteIssueResult(invite=invite, invite_token="plain-token")
    )

    response = client.post(
        "/api/v1/tenants/invites",
        json={"invited_email": "invitee@example.com", "role": "member"},
        headers=_headers(token=token, tenant_id=tenant_id, tenant_role="owner"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["invite_token"] == "plain-token"


def test_accept_invite_returns_session(
    client: TestClient, mock_invite_service: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_id = uuid4()
    result = TeamInviteAcceptResult(
        invite_id=uuid4(),
        user_id=uuid4(),
        tenant_id=tenant_id,
        email="invitee@example.com",
    )
    mock_invite_service.accept_invite_for_new_user = AsyncMock(return_value=result)

    now = datetime.now(UTC)
    tokens = UserSessionTokens(
        access_token="access",
        refresh_token="refresh",
        expires_at=now + timedelta(minutes=15),
        refresh_expires_at=now + timedelta(days=7),
        kid="kid",
        refresh_kid="rkid",
        scopes=["billing:read"],
        tenant_id=str(tenant_id),
        user_id=str(result.user_id),
        email_verified=True,
        session_id=str(uuid4()),
    )
    monkeypatch.setattr(
        "app.api.v1.tenants.routes_invites.auth_service.login_user",
        AsyncMock(return_value=tokens),
        raising=False,
    )

    response = client.post(
        "/api/v1/tenants/invites/accept",
        json={
            "token": "invite-token",
            "password": "ValidPassword!!123",
            "display_name": "Invitee",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["access_token"] == "access"
    assert body["tenant_id"] == str(tenant_id)
