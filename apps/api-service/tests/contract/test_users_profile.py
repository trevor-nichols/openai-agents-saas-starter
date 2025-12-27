"""Contract tests for user profile endpoints."""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])

from app.bootstrap import get_container
from app.core.security import get_token_signer
from app.core.settings import get_settings
from app.domain.users import UserProfileSummary
from main import app


@pytest.fixture
def client(fake_user_service) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        container = cast(Any, get_container())
        container.user_service = fake_user_service
        yield test_client


@pytest.fixture
def fake_user_service():
    stub = AsyncMock()
    stub.get_user_profile_summary = AsyncMock()
    return stub


def _mint_user_token(*, token_use: str, user_id: UUID, tenant_id: UUID) -> str:
    signer = get_token_signer()
    now = datetime.now(UTC)
    settings = get_settings()
    payload = {
        "sub": f"user:{user_id}",
        "scope": "conversations:read",
        "token_use": token_use,
        "iss": settings.app_name,
        "aud": settings.auth_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
        "tenant_id": str(tenant_id),
        "roles": ["admin"],
        "email_verified": True,
    }
    token = signer.sign(payload)
    return token.primary.token


def test_users_me_returns_profile(client: TestClient, fake_user_service) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    profile = UserProfileSummary(
        user_id=user_id,
        tenant_id=tenant_id,
        email="owner@example.com",
        display_name="Dev Admin",
        given_name="Dev",
        family_name="Admin",
        avatar_url="https://example.com/avatar.png",
        timezone="UTC",
        locale="en-US",
        role="owner",
        email_verified=True,
    )
    fake_user_service.get_user_profile_summary.return_value = profile
    token = _mint_user_token(token_use="access", user_id=user_id, tenant_id=tenant_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["user_id"] == str(user_id)
    assert body["data"]["tenant_id"] == str(tenant_id)
    assert body["data"]["email"] == profile.email
    assert body["data"]["display_name"] == profile.display_name
    assert body["data"]["avatar_url"] == profile.avatar_url
    assert body["data"]["timezone"] == profile.timezone
    assert body["data"]["locale"] == profile.locale

    fake_user_service.get_user_profile_summary.assert_awaited_once()
    kwargs = fake_user_service.get_user_profile_summary.await_args.kwargs
    assert kwargs["user_id"] == user_id
    assert kwargs["tenant_id"] == tenant_id


def test_users_me_rejects_refresh_token(client: TestClient) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    token = _mint_user_token(token_use="refresh", user_id=user_id, tenant_id=tenant_id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Access token required."
