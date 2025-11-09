"""Unit tests for the signup service orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.domain.billing import BillingPlan
from app.services.auth_service import UserSessionTokens
from app.services.billing_service import BillingService
from app.services.signup_service import EmailAlreadyRegisteredError, SignupService


class StubBillingService:
    def __init__(
        self,
        error: Exception | None = None,
        plans: list[BillingPlan] | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._error = error
        self._plans = plans or []

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
    ) -> None:
        if self._error:
            raise self._error
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "plan_code": plan_code,
                "billing_email": billing_email,
                "auto_renew": auto_renew,
                "seat_count": seat_count,
                "trial_days": trial_days,
            }
        )

    async def list_plans(self) -> list[BillingPlan]:
        return self._plans


@dataclass
class StubAuthService:
    tokens: UserSessionTokens

    async def login_user(self, **_: Any) -> UserSessionTokens:
        return self.tokens


@pytest.fixture(autouse=True)
def mock_email_verification(monkeypatch: pytest.MonkeyPatch):
    service = AsyncMock()
    service.send_verification_email = AsyncMock(return_value=True)

    def _get_service():
        return service

    monkeypatch.setattr("app.services.signup_service.get_email_verification_service", _get_service)
    return service


def _token_payload(user_id: str, tenant_id: str) -> UserSessionTokens:
    now = datetime.now(UTC)
    return UserSessionTokens(
        access_token="access",
        refresh_token="refresh",
        expires_at=now,
        refresh_expires_at=now,
        kid="kid",
        refresh_kid="refresh-kid",
        scopes=["conversations:read"],
        tenant_id=tenant_id,
        user_id=user_id,
        email_verified=False,
        session_id=str(uuid4()),
    )


def _patch_internals(
    service: SignupService,
    monkeypatch: pytest.MonkeyPatch,
    *,
    slug: str = "acme",
    provision_result: tuple[str, str] = ("tenant-1", "user-1"),
    provision_exc: Exception | None = None,
) -> None:
    async def fake_slug(self, _slug: str) -> str:
        return slug

    async def fake_provision(self, **_: Any) -> tuple[str, str]:
        if provision_exc:
            raise provision_exc
        return provision_result

    monkeypatch.setattr(SignupService, "_ensure_unique_slug", fake_slug, raising=False)
    monkeypatch.setattr(SignupService, "_provision_tenant_owner", fake_provision, raising=False)


@pytest.mark.asyncio
async def test_register_uses_plan_trial_when_override_disallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="month",
        interval_count=1,
        price_cents=2000,
        currency="usd",
        trial_days=21,
    )
    billing_stub = StubBillingService(plans=[plan])
    auth_stub = StubAuthService(tokens=_token_payload("user-1", "tenant-1"))
    monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: Settings(enable_billing=True),
    )
    _patch_internals(service, monkeypatch)

    result = await service.register(
        email="owner@example.com",
        password="IroncladValley$462",
        tenant_name="Acme",
        display_name="Acme Owner",
        plan_code="starter",
        trial_days=60,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert result.tenant_slug == "acme"
    assert billing_stub.calls and billing_stub.calls[0]["plan_code"] == "starter"
    assert billing_stub.calls[0]["trial_days"] == 21


@pytest.mark.asyncio
async def test_register_allows_shorter_trial_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="month",
        interval_count=1,
        price_cents=2000,
        currency="usd",
        trial_days=30,
    )
    billing_stub = StubBillingService(plans=[plan])
    auth_stub = StubAuthService(tokens=_token_payload("user-flag", "tenant-flag"))
    monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: Settings(enable_billing=True, allow_signup_trial_override=True),
    )
    _patch_internals(service, monkeypatch)

    await service.register(
        email="flag@example.com",
        password="IroncladValley$462",
        tenant_name="Flag",
        display_name=None,
        plan_code="starter",
        trial_days=5,
        ip_address=None,
        user_agent=None,
    )

    assert billing_stub.calls and billing_stub.calls[0]["trial_days"] == 5


@pytest.mark.asyncio
async def test_register_clamps_override_to_plan_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="month",
        interval_count=1,
        price_cents=2000,
        currency="usd",
        trial_days=10,
    )
    billing_stub = StubBillingService(plans=[plan])
    auth_stub = StubAuthService(tokens=_token_payload("user-clamp", "tenant-clamp"))
    monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: Settings(enable_billing=True, allow_signup_trial_override=True),
    )
    _patch_internals(service, monkeypatch)

    await service.register(
        email="clamp@example.com",
        password="IroncladValley$462",
        tenant_name="Clamp",
        display_name=None,
        plan_code="starter",
        trial_days=45,
        ip_address=None,
        user_agent=None,
    )

    assert billing_stub.calls and billing_stub.calls[0]["trial_days"] == 10


@pytest.mark.asyncio
async def test_register_propagates_duplicate_email(monkeypatch: pytest.MonkeyPatch) -> None:
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-2", "tenant-2"))
    monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: Settings(enable_billing=False),
    )
    _patch_internals(
        service,
        monkeypatch,
        provision_exc=EmailAlreadyRegisteredError("duplicate"),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(
            email="owner@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code=None,
            trial_days=None,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_register_surfaces_billing_plan_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.billing_service import PlanNotFoundError

    billing_stub = StubBillingService(error=PlanNotFoundError("unknown plan"))
    auth_stub = StubAuthService(tokens=_token_payload("user-3", "tenant-3"))
    monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: Settings(enable_billing=True),
    )
    _patch_internals(service, monkeypatch)

    with pytest.raises(PlanNotFoundError):
        await service.register(
            email="owner3@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code="unknown",
            trial_days=None,
            ip_address=None,
            user_agent=None,
        )
