"""Unit tests for the signup service orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.bootstrap import get_container
from app.core.settings import Settings
from app.domain.billing import BillingPlan
from app.services.auth_service import UserSessionTokens
from app.services.billing.billing_service import BillingService
from app.services.signup.invite_service import (
    InviteEmailMismatchError,
    InviteNotFoundError,
    InviteService,
    InviteTokenRequiredError,
)
from app.services.signup.signup_service import (
    EmailAlreadyRegisteredError,
    PublicSignupDisabledError,
    SignupService,
)


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


def _default_invite_status() -> Any:
    return type("Status", (), {"value": "active"})()


@dataclass
class StubInvite:
    id: str = "invite-1"
    token_hint: str = "abcdef12"
    invited_email: str | None = None
    status: Any = field(default_factory=_default_invite_status)
    max_redemptions: int = 1
    redeemed_count: int = 0
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    signup_request_id: str | None = None
    note: str | None = None


@dataclass
class StubInviteReservationContext:
    invite: StubInvite = field(default_factory=StubInvite)
    finalized_with: list[dict[str, str]] = field(default_factory=list)
    releases: list[str] = field(default_factory=list)
    finalized: bool = False
    released: bool = False

    async def mark_succeeded(self, *, tenant_id: str, user_id: str) -> None:
        self.finalized_with.append({"tenant_id": tenant_id, "user_id": user_id})
        self.finalized = True

    async def ensure_released(self, *, reason: str) -> None:
        if self.finalized or self.released:
            return
        self.releases.append(reason)
        self.released = True


class StubInviteService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.context = StubInviteReservationContext()
        self._error = error

    async def reserve_for_signup(
        self,
        *,
        token: str | None,
        email: str,
        require_request: bool,
    ) -> StubInviteReservationContext:
        self.calls.append({"token": token, "email": email, "require_request": require_request})
        if not token:
            raise InviteTokenRequiredError("Invite required")
        if self._error:
            raise self._error
        return self.context


@pytest.fixture(autouse=True)
def mock_email_verification():
    service = AsyncMock()
    service.send_verification_email = AsyncMock(return_value=True)
    cast(Any, get_container()).email_verification_service = service
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


def _build_settings(**overrides: Any) -> Settings:
    # Use an explicit empty env file to avoid leaking repo-level .env.local defaults
    # (which currently set SIGNUP_ACCESS_POLICY=public). Tests supply the desired
    # policy via overrides, so keep the environment out of the equation.
    return Settings(_env_file=None, **overrides)  # pyright: ignore[reportCallIssue]


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
    cast(Any, get_container()).auth_service = auth_stub

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(
            enable_billing=True,
            signup_access_policy="public",
        ),
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
        invite_token=None,
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
    cast(Any, get_container()).auth_service = auth_stub

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(
            enable_billing=True,
            allow_signup_trial_override=True,
            signup_access_policy="public",
        ),
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
        invite_token=None,
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
    cast(Any, get_container()).auth_service = auth_stub

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(
            enable_billing=True,
            allow_signup_trial_override=True,
            signup_access_policy="public",
        ),
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
        invite_token=None,
    )

    assert billing_stub.calls and billing_stub.calls[0]["trial_days"] == 10


@pytest.mark.asyncio
async def test_register_propagates_duplicate_email(monkeypatch: pytest.MonkeyPatch) -> None:
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-2", "tenant-2"))
    cast(Any, get_container()).auth_service = auth_stub

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(
            enable_billing=False,
            signup_access_policy="public",
        ),
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
            invite_token=None,
        )


@pytest.mark.asyncio
async def test_register_surfaces_billing_plan_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.billing.billing_service import PlanNotFoundError

    billing_stub = StubBillingService(error=PlanNotFoundError("unknown plan"))
    auth_stub = StubAuthService(tokens=_token_payload("user-3", "tenant-3"))
    cast(Any, get_container()).auth_service = auth_stub

    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(
            enable_billing=True,
            signup_access_policy="public",
        ),
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
            invite_token=None,
        )


@pytest.mark.asyncio
async def test_register_requires_invite_under_invite_only_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNUP_ACCESS_POLICY", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_SIGNUP", raising=False)
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-4", "tenant-4"))
    cast(Any, get_container()).auth_service = auth_stub

    invite_stub = StubInviteService()
    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(signup_access_policy="invite_only"),
        invite_service=cast(InviteService, invite_stub),
    )
    _patch_internals(service, monkeypatch)

    with pytest.raises(PublicSignupDisabledError):
        await service.register(
            email="invite-only@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code=None,
            trial_days=None,
            ip_address=None,
            user_agent=None,
            invite_token=None,
        )


@pytest.mark.asyncio
async def test_register_consumes_invite_when_token_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNUP_ACCESS_POLICY", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_SIGNUP", raising=False)
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-5", "tenant-5"))
    cast(Any, get_container()).auth_service = auth_stub

    invite_stub = StubInviteService()
    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(signup_access_policy="invite_only"),
        invite_service=cast(InviteService, invite_stub),
    )
    _patch_internals(service, monkeypatch)

    await service.register(
        email="invite-token@example.com",
        password="IroncladValley$462",
        tenant_name="Acme",
        display_name=None,
        plan_code=None,
        trial_days=None,
        ip_address=None,
        user_agent=None,
        invite_token="token-123",
    )

    assert invite_stub.calls and invite_stub.calls[0]["token"] == "token-123"
    assert invite_stub.context.finalized_with
    assert invite_stub.context.finalized_with[0]["tenant_id"] == "tenant-1"
    assert not invite_stub.context.releases


@pytest.mark.asyncio
async def test_register_invalid_invite_maps_to_public_signup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNUP_ACCESS_POLICY", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_SIGNUP", raising=False)
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-err", "tenant-err"))
    cast(Any, get_container()).auth_service = auth_stub

    invite_stub = StubInviteService(error=InviteNotFoundError("Invite token is invalid."))
    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(signup_access_policy="invite_only"),
        invite_service=cast(InviteService, invite_stub),
    )
    _patch_internals(service, monkeypatch)

    with pytest.raises(PublicSignupDisabledError):
        await service.register(
            email="invalid-token@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code=None,
            trial_days=None,
            ip_address=None,
            user_agent=None,
            invite_token="bad-token",
        )


@pytest.mark.asyncio
async def test_register_email_mismatch_maps_to_public_signup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNUP_ACCESS_POLICY", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_SIGNUP", raising=False)
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-err", "tenant-err"))
    cast(Any, get_container()).auth_service = auth_stub

    invite_stub = StubInviteService(error=InviteEmailMismatchError("Invite token is restricted"))
    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(signup_access_policy="invite_only"),
        invite_service=cast(InviteService, invite_stub),
    )
    _patch_internals(service, monkeypatch)

    with pytest.raises(PublicSignupDisabledError):
        await service.register(
            email="wrong@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code=None,
            trial_days=None,
            ip_address=None,
            user_agent=None,
            invite_token="token-xyz",
        )


@pytest.mark.asyncio
async def test_register_releases_invite_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNUP_ACCESS_POLICY", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_SIGNUP", raising=False)
    billing_stub = StubBillingService()
    auth_stub = StubAuthService(tokens=_token_payload("user-err", "tenant-err"))
    cast(Any, get_container()).auth_service = auth_stub

    invite_stub = StubInviteService()
    service = SignupService(
        billing=cast(BillingService, billing_stub),
        settings_factory=lambda: _build_settings(signup_access_policy="invite_only"),
        invite_service=cast(InviteService, invite_stub),
    )
    _patch_internals(
        service,
        monkeypatch,
        provision_exc=EmailAlreadyRegisteredError("duplicate"),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(
            email="invite-failure@example.com",
            password="IroncladValley$462",
            tenant_name="Acme",
            display_name=None,
            plan_code=None,
            trial_days=None,
            ip_address=None,
            user_agent=None,
            invite_token="token-err",
        )

    assert invite_stub.calls
    assert invite_stub.context.finalized_with == []
    assert invite_stub.context.releases == ["signup_failed"]
