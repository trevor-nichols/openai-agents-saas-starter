"""Focused unit tests for signup request service helpers."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import pytest

from app.core.settings import Settings
from app.domain.signup import (
    SignupRequest,
    SignupRequestCreate,
    SignupRequestListResult,
    SignupRequestRepository,
    SignupRequestStatus,
)
from app.services.shared.rate_limit_service import hash_user_agent
from app.services.signup.invite_service import InviteService
from app.services.signup.signup_request_service import (
    SignupRequestQuotaExceededError,
    SignupRequestService,
    _normalize_uuid,
)


class StubSignupRequestRepository(SignupRequestRepository):
    def __init__(self) -> None:
        self.created_payload: SignupRequestCreate | None = None
        self.pending_count = 0

    async def create(self, payload: SignupRequestCreate) -> SignupRequest:
        self.created_payload = payload
        return SignupRequest(
            id=uuid4(),
            email=payload.email,
            organization=payload.organization,
            full_name=payload.full_name,
            message=payload.message,
            status=SignupRequestStatus.PENDING,
            decision_reason=None,
            decided_at=None,
            decided_by=None,
            signup_invite_token_hint=None,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
            honeypot_value=payload.honeypot_value,
            metadata=payload.metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def count_pending_requests_by_ip(self, ip_address: str) -> int:
        return self.pending_count

    async def get(self, request_id):  # pragma: no cover - not needed in tests
        return None

    async def list_requests(
        self,
        *,
        status,
        limit,
        offset,
    ) -> SignupRequestListResult:  # pragma: no cover
        return SignupRequestListResult(requests=[], total=0)

    async def transition_status(
        self,
        *,
        request_id,
        expected_status,
        new_status,
        decided_by,
        decided_at,
        decision_reason,
        invite_token_hint,
    ) -> SignupRequest | None:  # pragma: no cover
        return None


def test_normalize_uuid_accepts_uuid_instance() -> None:
    sample = uuid4()

    assert _normalize_uuid(sample) == sample


def test_normalize_uuid_accepts_string_representation() -> None:
    sample = uuid4()

    assert _normalize_uuid(str(sample)) == sample


def test_normalize_uuid_returns_none_for_invalid_string() -> None:
    assert _normalize_uuid("not-a-uuid") is None


def test_normalize_uuid_returns_none_for_blank_input() -> None:
    assert _normalize_uuid("   ") is None


@pytest.mark.asyncio
async def test_submit_request_blocks_honeypot(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = StubSignupRequestRepository()
    settings = Settings.model_validate({"signup_concurrent_requests_limit": 3})
    dummy_invite = cast(InviteService, object())
    service = SignupRequestService(
        repository=repo,
        settings_factory=lambda: settings,
        invite_service=dummy_invite,
    )

    reasons: list[str | None] = []

    monkeypatch.setattr(
        "app.services.signup.signup_request_service.record_signup_blocked",
        lambda *, reason: reasons.append(reason),
    )

    result = await service.submit_request(
        email="bot@example.com",
        organization="Org",
        full_name="Bot",
        message="spam",
        ip_address="10.0.0.1",
        user_agent="curl",
        honeypot_value="gotcha",
    )

    assert result is None
    assert repo.created_payload is None
    assert reasons == ["honeypot"]


@pytest.mark.asyncio
async def test_submit_request_enforces_concurrent_limit() -> None:
    repo = StubSignupRequestRepository()
    repo.pending_count = 5
    settings = Settings.model_validate({"signup_concurrent_requests_limit": 1})
    dummy_invite = cast(InviteService, object())
    service = SignupRequestService(
        repository=repo,
        settings_factory=lambda: settings,
        invite_service=dummy_invite,
    )

    with pytest.raises(SignupRequestQuotaExceededError):
        await service.submit_request(
            email="ops@example.com",
            organization="Ops",
            full_name="Ops User",
            message="hi",
            ip_address="203.0.113.5",
            user_agent="Mozilla/5.0",
            honeypot_value=None,
        )

    assert repo.created_payload is None


@pytest.mark.asyncio
async def test_submit_request_persists_fingerprint() -> None:
    repo = StubSignupRequestRepository()
    repo.pending_count = 0
    settings = Settings.model_validate({"signup_concurrent_requests_limit": 5})
    dummy_invite = cast(InviteService, object())
    service = SignupRequestService(
        repository=repo,
        settings_factory=lambda: settings,
        invite_service=dummy_invite,
    )

    await service.submit_request(
        email="user@example.com",
        organization="Acme",
        full_name="Acme User",
        message="Use case",
        ip_address="198.51.100.5",
        user_agent="Mozilla/5.0",
        honeypot_value=None,
    )

    assert repo.created_payload is not None
    assert repo.created_payload.metadata is not None
    assert (
        repo.created_payload.metadata["user_agent_fingerprint"]
        == hash_user_agent("Mozilla/5.0")
    )
