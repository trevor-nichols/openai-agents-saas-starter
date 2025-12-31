"""Contract tests for signup/register failure mappings."""

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
from app.services.billing.errors import (
    BillingError,
    InvalidTenantIdentifierError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
)
from app.services.signup.invite_service import (
    InviteExpiredError,
    InviteRequestMismatchError,
    InviteRevokedError,
    InviteTokenRequiredError,
)
from app.services.signup.signup_service import (
    BillingProvisioningError,
    EmailAlreadyRegisteredError,
    PublicSignupDisabledError,
    TenantSlugCollisionError,
)
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Spin up the FastAPI test client and install mocked services."""

    with TestClient(app) as test_client:
        container = cast(Any, get_container())
        container.signup_service = AsyncMock()
        yield test_client


def _base_payload() -> dict[str, Any]:
    return {
        "email": "owner@example.com",
        "password": "IroncladValley$462",
        "tenant_name": "Acme",
        "display_name": "Acme Owner",
        "plan_code": None,
        "trial_days": None,
        "accept_terms": True,
        "invite_token": None,
    }


def _register(client: TestClient, *, payload: dict[str, Any]) -> Any:
    return client.post("/api/v1/auth/register", json=payload)


@pytest.mark.parametrize(
    "error",
    [
        PublicSignupDisabledError("Public signup disabled"),
        InviteTokenRequiredError("Invite required"),
        InviteExpiredError("Invite expired"),
        InviteRevokedError("Invite revoked"),
        InviteRequestMismatchError("Invite mismatch"),
    ],
)
def test_register_invite_errors_return_403(client: TestClient, error: Exception) -> None:
    container = cast(Any, get_container())
    container.signup_service.register = AsyncMock(side_effect=error)

    response = _register(client, payload=_base_payload())

    assert response.status_code == 403
    body = response.json()
    assert body["error"] == "Forbidden"
    assert body["message"] == str(error)


@pytest.mark.parametrize(
    "error",
    [
        EmailAlreadyRegisteredError("Email already registered."),
        TenantSlugCollisionError("Tenant slug already exists."),
    ],
)
def test_register_conflicts_return_409(client: TestClient, error: Exception) -> None:
    container = cast(Any, get_container())
    container.signup_service.register = AsyncMock(side_effect=error)

    response = _register(client, payload=_base_payload())

    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "Conflict"
    assert body["message"] == str(error)


def test_register_billing_provisioning_error_returns_502(client: TestClient) -> None:
    error = BillingProvisioningError("Billing failed")
    container = cast(Any, get_container())
    container.signup_service.register = AsyncMock(side_effect=error)

    response = _register(client, payload=_base_payload())

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == "BadGateway"
    assert body["message"] == str(error)


@pytest.mark.parametrize(
    "error, expected_status",
    [
        (PlanNotFoundError("Unknown plan"), 404),
        (SubscriptionStateError("Subscription state conflict"), 409),
        (InvalidTenantIdentifierError("Invalid tenant"), 400),
        (SubscriptionNotFoundError("Subscription missing"), 400),
        (BillingError("Generic billing error"), 400),
    ],
)
def test_register_billing_errors_map_to_expected_status(
    client: TestClient,
    error: BillingError,
    expected_status: int,
) -> None:
    container = cast(Any, get_container())
    container.signup_service.register = AsyncMock(side_effect=error)

    response = _register(client, payload=_base_payload())

    assert response.status_code == expected_status
    body = response.json()
    expected_error = "BadRequest"
    if expected_status == 404:
        expected_error = "NotFound"
    elif expected_status == 409:
        expected_error = "Conflict"
    assert body["error"] == expected_error
    assert body["message"] == str(error)


@pytest.mark.parametrize("field", ["email", "password", "tenant_name"])
def test_register_validation_errors_return_422(client: TestClient, field: str) -> None:
    payload = _base_payload()
    payload[field] = ""

    response = _register(client, payload=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "ValidationError"
    assert body["message"] == "Request validation failed."


@pytest.mark.parametrize("policy", ["invite_only", "approval"])
def test_register_rejects_missing_invite_token_when_required(
    client: TestClient, policy: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SIGNUP_ACCESS_POLICY", policy)
    container = cast(Any, get_container())
    container.signup_service.register = AsyncMock(
        side_effect=PublicSignupDisabledError("Invite required")
    )

    response = _register(client, payload=_base_payload())

    assert response.status_code == 403
    body = response.json()
    assert body["error"] == "Forbidden"


def test_register_honors_rate_limit_errors(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from starlette import status

    monkeypatch.setattr(
        "app.api.v1.auth.routes_signup._enforce_signup_quota",
        AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        ),
    )

    response = _register(client, payload=_base_payload())

    assert response.status_code == 429
    body = response.json()
    assert body["error"] == "TooManyRequests"


def test_register_success_returns_201(client: TestClient) -> None:
    container = cast(Any, get_container())
    result = AsyncMock()
    result.tenant_slug = "acme"
    session_id = uuid4()
    result.session = AsyncMock()
    result.session.access_token = "access"
    result.session.refresh_token = "refresh"
    result.session.token_type = "bearer"
    result.session.kid = "kid"
    result.session.refresh_kid = "refresh-kid"
    now = datetime.now(UTC)
    result.session.expires_at = now + timedelta(minutes=15)
    result.session.refresh_expires_at = now + timedelta(days=7)
    result.session.scopes = ["conversations:read"]
    result.session.tenant_id = str(uuid4())
    result.session.user_id = str(uuid4())
    result.session.email_verified = False
    result.session.session_id = str(session_id)
    container.signup_service.register = AsyncMock(return_value=result)

    response = _register(client, payload=_base_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_slug"] == "acme"
    assert body["access_token"] == "access"
