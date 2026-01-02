"""Contract tests for SSO endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.bootstrap import get_container
from app.domain.auth import UserSessionTokens
from app.domain.sso import SsoAutoProvisionPolicy, SsoProviderConfig, SsoTokenAuthMethod
from app.domain.tenant_roles import TenantRole
from app.services.auth.errors import MfaRequiredError, UserAuthenticationError
from app.services.sso import SsoConfigurationError, SsoStartResult, SsoTokenError
from app.services.users import UserLockedError
from main import app


def _tokens() -> UserSessionTokens:
    now = datetime.now(UTC)
    return UserSessionTokens(
        access_token="access",
        refresh_token="refresh",
        expires_at=now,
        refresh_expires_at=now,
        kid="kid",
        refresh_kid="kid",
        scopes=["scope"],
        tenant_id=str(uuid4()),
        user_id=str(uuid4()),
        email_verified=True,
        session_id=str(uuid4()),
    )


def _provider_config(provider_key: str = "google") -> SsoProviderConfig:
    now = datetime.now(UTC)
    return SsoProviderConfig(
        id=uuid4(),
        tenant_id=uuid4(),
        provider_key=provider_key,
        enabled=True,
        issuer_url="https://accounts.google.com",
        client_id="client-id",
        client_secret="secret",
        discovery_url=None,
        scopes=["openid", "email", "profile"],
        pkce_required=True,
        token_endpoint_auth_method=SsoTokenAuthMethod.CLIENT_SECRET_POST,
        allowed_id_token_algs=[],
        auto_provision_policy=SsoAutoProvisionPolicy.INVITE_ONLY,
        allowed_domains=[],
        default_role=TenantRole.MEMBER,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def fake_sso_service():
    service = AsyncMock()
    service.start_sso = AsyncMock(
        return_value=SsoStartResult(
            authorize_url="https://auth.example.com/authorize",
            state="state",
        )
    )
    service.complete_sso = AsyncMock(return_value=_tokens())
    service.list_providers = AsyncMock(return_value=[_provider_config()])
    return service


@pytest.fixture
def client(fake_sso_service) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        container = cast(Any, get_container())
        container.sso_service = fake_sso_service
        yield test_client


def test_list_sso_providers(client: TestClient) -> None:
    tenant_id = str(uuid4())
    resp = client.get(f"/api/v1/auth/sso/providers?tenant_id={tenant_id}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["providers"][0]["provider_key"] == "google"
    assert body["providers"][0]["display_name"] == "Google"


def test_list_sso_providers_rejects_invalid_tenant_id(client: TestClient) -> None:
    resp = client.get("/api/v1/auth/sso/providers?tenant_id=not-a-uuid")

    assert resp.status_code == 400, resp.text


def test_list_sso_providers_requires_single_tenant_selector(client: TestClient) -> None:
    resp = client.get("/api/v1/auth/sso/providers")

    assert resp.status_code == 400, resp.text

    tenant_id = str(uuid4())
    resp = client.get(f"/api/v1/auth/sso/providers?tenant_id={tenant_id}&tenant_slug=slug")
    assert resp.status_code == 400, resp.text


def test_start_sso_returns_authorize_url(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/sso/google/start",
        json={"tenant_id": str(uuid4())},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["authorize_url"].startswith("https://auth.example.com")


def test_start_sso_rejects_invalid_tenant_id(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/sso/google/start",
        json={"tenant_id": "not-a-uuid"},
    )

    assert resp.status_code == 400, resp.text


def test_start_sso_requires_tenant_selection(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/sso/google/start",
        json={},
    )

    assert resp.status_code == 409, resp.text

    resp = client.post(
        "/api/v1/auth/sso/google/start",
        json={"tenant_id": str(uuid4()), "tenant_slug": "slug"},
    )

    assert resp.status_code == 400, resp.text


def test_callback_returns_tokens(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/sso/google/callback",
        json={"code": "code", "state": "state"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"] == "access"
    assert body["refresh_token"] == "refresh"


def test_callback_returns_mfa_challenge(fake_sso_service, client: TestClient) -> None:
    fake_sso_service.complete_sso.side_effect = MfaRequiredError(
        "challenge",
        [
            {
                "id": str(uuid4()),
                "method_type": "totp",
                "label": "Authenticator",
                "verified_at": None,
                "last_used_at": None,
                "revoked_at": None,
            }
        ],
    )

    resp = client.post(
        "/api/v1/auth/sso/google/callback",
        json={"code": "code", "state": "state"},
    )

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["challenge_token"] == "challenge"
    assert body["methods"][0]["method_type"] == "totp"


def test_callback_maps_token_verification_error(client: TestClient, fake_sso_service) -> None:
    fake_sso_service.complete_sso.side_effect = SsoTokenError(
        "Invalid ID token.",
        reason="token_verification_failed",
    )

    resp = client.post(
        "/api/v1/auth/sso/google/callback",
        json={"code": "code", "state": "state"},
    )

    assert resp.status_code == 401, resp.text


def test_start_maps_provider_disabled(client: TestClient, fake_sso_service) -> None:
    fake_sso_service.start_sso.side_effect = SsoConfigurationError(
        "SSO provider is disabled.",
        reason="provider_disabled",
    )

    resp = client.post(
        "/api/v1/auth/sso/google/start",
        json={"tenant_id": str(uuid4())},
    )

    assert resp.status_code == 403, resp.text


def test_callback_maps_auth_failure(client: TestClient, fake_sso_service) -> None:
    exc = UserAuthenticationError("User locked.")
    exc.__cause__ = UserLockedError("User locked.")
    fake_sso_service.complete_sso.side_effect = exc

    resp = client.post(
        "/api/v1/auth/sso/google/callback",
        json={"code": "code", "state": "state"},
    )

    assert resp.status_code == 423, resp.text
