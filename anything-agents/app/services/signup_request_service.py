"""Service orchestrating signup requests and approvals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.config import Settings, get_settings
from app.domain.signup import (
    SignupRequest,
    SignupRequestCreate,
    SignupRequestListResult,
    SignupRequestRepository,
    SignupRequestStatus,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.signup_repository import (
    PostgresSignupRequestRepository,
)
from app.observability.logging import log_event
from app.observability.metrics import record_signup_blocked
from app.services.invite_service import (
    InviteIssueResult,
    InviteService,
    build_invite_service,
    get_invite_service,
)
from app.services.rate_limit_service import hash_user_agent


@dataclass(slots=True)
class SignupRequestDecisionResult:
    request: SignupRequest
    invite: InviteIssueResult | None = None


class SignupRequestServiceError(RuntimeError):
    """Base error for request workflows."""


class SignupRequestNotFoundError(SignupRequestServiceError):
    """Raised when a request cannot be located."""


class SignupRequestQuotaExceededError(SignupRequestServiceError):
    """Raised when request quotas prevent accepting additional submissions."""

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class SignupRequestService:
    def __init__(
        self,
        *,
        repository: SignupRequestRepository | None = None,
        invite_service: InviteService | None = None,
        settings_factory: Callable[[], Settings] | None = None,
    ) -> None:
        self._repository = repository or PostgresSignupRequestRepository(get_async_sessionmaker())
        self._invite_service = invite_service or get_invite_service()
        self._settings_factory = settings_factory or get_settings

    @property
    def repository(self) -> SignupRequestRepository:
        return self._repository

    @property
    def invite_service(self) -> InviteService:
        return self._invite_service

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    async def submit_request(
        self,
        *,
        email: str,
        organization: str | None,
        full_name: str | None,
        message: str | None,
        ip_address: str | None,
        user_agent: str | None,
        honeypot_value: str | None,
    ) -> SignupRequest | None:
        settings = self._get_settings()
        metadata: dict[str, Any] | None = None
        fingerprint = hash_user_agent(user_agent)
        if fingerprint:
            metadata = {"user_agent_fingerprint": fingerprint}

        normalized_honeypot = _optional_str(honeypot_value)
        if normalized_honeypot:
            metadata = metadata or {}
            metadata["suspected_bot"] = True
            log_event(
                "signup.request_blocked",
                result="honeypot",
                email=email,
                ip_address=_optional_str(ip_address),
            )
            record_signup_blocked(reason="honeypot")
            return None

        normalized_ip = _optional_str(ip_address)
        if (
            normalized_ip
            and settings.signup_concurrent_requests_limit > 0
            and await self.repository.count_pending_requests_by_ip(normalized_ip)
            >= settings.signup_concurrent_requests_limit
        ):
            raise SignupRequestQuotaExceededError(
                "Too many pending requests from this IP. Try again soon.",
                reason="pending_limit",
            )

        payload = SignupRequestCreate(
            email=email.strip().lower(),
            organization=_optional_str(organization),
            full_name=_optional_str(full_name),
            message=_optional_str(message),
            ip_address=normalized_ip,
            user_agent=_optional_str(user_agent),
            honeypot_value=None,
            metadata=metadata,
        )
        record = await self.repository.create(payload)
        log_event(
            "signup.request_submitted",
            result="success",
            request_id=str(record.id),
        )
        return record

    async def list_requests(
        self,
        *,
        status: SignupRequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SignupRequestListResult:
        return await self.repository.list_requests(status=status, limit=limit, offset=offset)

    async def approve_request(
        self,
        request_id: UUID,
        *,
        actor_user_id: str | UUID,
        note: str | None,
        invite_expires_in_hours: int | None,
    ) -> SignupRequestDecisionResult:
        request = await self._get_request_or_error(request_id)
        invite = await self.invite_service.issue_invite(
            issuer_user_id=actor_user_id,
            issuer_tenant_id=None,
            invited_email=request.email,
            max_redemptions=1,
            expires_in_hours=invite_expires_in_hours,
            note=note,
            signup_request_id=request.id,
        )
        timestamp = datetime.now(UTC)
        actor_uuid = _normalize_uuid(actor_user_id)
        if actor_uuid is None:
            raise SignupRequestServiceError("Actor user id is required to approve requests.")

        updated = await self.repository.transition_status(
            request_id=request.id,
            expected_status=SignupRequestStatus.PENDING,
            new_status=SignupRequestStatus.APPROVED,
            decided_by=actor_uuid,
            decided_at=timestamp,
            decision_reason=note,
            invite_token_hint=invite.invite.token_hint,
        )
        if updated is None:
            await self.invite_service.revoke_invite(
                invite.invite.id,
                reason="request_state_changed",
            )
            raise SignupRequestServiceError("Request already processed by another operator.")
        log_event(
            "signup.request_approved",
            result="success",
            request_id=str(request.id),
            invite_id=str(invite.invite.id),
        )
        return SignupRequestDecisionResult(request=updated, invite=invite)

    async def reject_request(
        self,
        request_id: UUID,
        *,
        actor_user_id: str | UUID,
        reason: str | None,
    ) -> SignupRequestDecisionResult:
        request = await self._get_request_or_error(request_id)
        timestamp = datetime.now(UTC)
        actor_uuid = _normalize_uuid(actor_user_id)
        if actor_uuid is None:
            raise SignupRequestServiceError("Actor user id is required to reject requests.")

        updated = await self.repository.transition_status(
            request_id=request.id,
            expected_status=SignupRequestStatus.PENDING,
            new_status=SignupRequestStatus.REJECTED,
            decided_by=actor_uuid,
            decided_at=timestamp,
            decision_reason=reason,
            invite_token_hint=None,
        )
        if updated is None:
            raise SignupRequestServiceError("Request already processed by another operator.")
        log_event(
            "signup.request_rejected",
            result="success",
            request_id=str(request.id),
        )
        return SignupRequestDecisionResult(request=updated)

    async def get_request(self, request_id: UUID) -> SignupRequest | None:
        normalized = _normalize_uuid(request_id)
        if normalized is None:
            return None
        return await self.repository.get(normalized)

    async def _get_request_or_error(self, request_id: UUID) -> SignupRequest:
        record = await self.get_request(request_id)
        if record is None:
            raise SignupRequestNotFoundError("Signup request not found.")
        return record


def _optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return UUID(stripped)
    except ValueError:
        return None


def build_signup_request_service(
    *,
    repository: SignupRequestRepository | None = None,
    invite_service: InviteService | None = None,
    settings_factory: Callable[[], Settings] | None = None,
) -> SignupRequestService:
    invite = invite_service or build_invite_service()
    repo = repository or PostgresSignupRequestRepository(get_async_sessionmaker())
    return SignupRequestService(
        repository=repo,
        invite_service=invite,
        settings_factory=settings_factory,
    )


def get_signup_request_service() -> SignupRequestService:
    from app.bootstrap.container import get_container

    container = get_container()
    service = container.signup_request_service
    if service is None:
        repository = PostgresSignupRequestRepository(get_async_sessionmaker())
        invite = get_invite_service()
        container.signup_request_service = build_signup_request_service(
            repository=repository,
            invite_service=invite,
        )
        service = container.signup_request_service
    assert service is not None
    return service


__all__ = [
    "SignupRequestDecisionResult",
    "SignupRequestNotFoundError",
    "SignupRequestQuotaExceededError",
    "SignupRequestService",
    "SignupRequestServiceError",
    "build_signup_request_service",
    "get_signup_request_service",
]
