"""Domain models and repository protocols for signup guardrails."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol
from uuid import UUID


class SignupInviteStatus(str, Enum):
    """Lifecycle states for tenant signup invites."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"


class SignupInviteReservationStatus(str, Enum):
    """State machine for invite reservation attempts during signup."""

    ACTIVE = "active"
    RELEASED = "released"
    FINALIZED = "finalized"
    EXPIRED = "expired"


@dataclass(slots=True)
class SignupInvite:
    """Persisted invite metadata used to gate public signup."""

    id: UUID
    token_hash: str
    token_hint: str
    invited_email: str | None
    issuer_user_id: UUID | None
    issuer_tenant_id: UUID | None
    signup_request_id: UUID | None
    status: SignupInviteStatus
    max_redemptions: int
    redeemed_count: int
    expires_at: datetime | None
    last_redeemed_at: datetime | None
    revoked_at: datetime | None
    revoked_reason: str | None
    note: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class SignupInviteReservation:
    """Represents a temporary claim on an invite while signup runs."""

    id: UUID
    invite_id: UUID
    email: str
    status: SignupInviteReservationStatus
    reserved_at: datetime
    expires_at: datetime
    released_at: datetime | None
    released_reason: str | None
    finalized_at: datetime | None
    tenant_id: UUID | None
    user_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class SignupInviteCreate:
    """Payload used by repositories to persist invites."""

    token_hash: str
    token_hint: str
    invited_email: str | None
    issuer_user_id: UUID | None
    issuer_tenant_id: UUID | None
    signup_request_id: UUID | None
    max_redemptions: int
    expires_at: datetime | None
    note: str | None
    metadata: dict[str, Any] | None


@dataclass(slots=True)
class SignupInviteListResult:
    invites: list[SignupInvite]
    total: int


class SignupInviteRepository(Protocol):
    async def create(self, payload: SignupInviteCreate) -> SignupInvite: ...

    async def get(self, invite_id: UUID) -> SignupInvite | None: ...

    async def find_by_token_hash(self, token_hash: str) -> SignupInvite | None: ...

    async def mark_redeemed(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
    ) -> SignupInvite | None: ...

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        reason: str | None,
    ) -> SignupInvite | None: ...

    async def reserve_invite(
        self,
        invite_id: UUID,
        *,
        email: str,
        now: datetime,
        expires_at: datetime,
    ) -> SignupInviteReservation | None: ...

    async def finalize_reservation(
        self,
        reservation_id: UUID,
        *,
        tenant_id: UUID,
        user_id: UUID,
        timestamp: datetime,
    ) -> SignupInviteReservation | None: ...

    async def release_reservation(
        self,
        reservation_id: UUID,
        *,
        timestamp: datetime,
        reason: str | None,
    ) -> SignupInviteReservation | None: ...

    async def list_invites(
        self,
        *,
        status: SignupInviteStatus | None,
        email: str | None,
        signup_request_id: UUID | None,
        limit: int,
        offset: int,
    ) -> SignupInviteListResult: ...


class SignupRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True)
class SignupRequest:
    id: UUID
    email: str
    organization: str | None
    full_name: str | None
    message: str | None
    status: SignupRequestStatus
    decision_reason: str | None
    decided_at: datetime | None
    decided_by: UUID | None
    signup_invite_token_hint: str | None
    ip_address: str | None
    user_agent: str | None
    honeypot_value: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class SignupRequestCreate:
    email: str
    organization: str | None
    full_name: str | None
    message: str | None
    ip_address: str | None
    user_agent: str | None
    honeypot_value: str | None
    metadata: dict[str, Any] | None


@dataclass(slots=True)
class SignupRequestListResult:
    requests: list[SignupRequest]
    total: int


class SignupRequestRepository(Protocol):
    async def create(self, payload: SignupRequestCreate) -> SignupRequest: ...

    async def get(self, request_id: UUID) -> SignupRequest | None: ...

    async def list_requests(
        self,
        *,
        status: SignupRequestStatus | None,
        limit: int,
        offset: int,
    ) -> SignupRequestListResult: ...

    async def transition_status(
        self,
        *,
        request_id: UUID,
        expected_status: SignupRequestStatus,
        new_status: SignupRequestStatus,
        decided_by: UUID,
        decided_at: datetime,
        decision_reason: str | None,
        invite_token_hint: str | None,
    ) -> SignupRequest | None: ...


__all__ = [
    "SignupInvite",
    "SignupInviteCreate",
    "SignupInviteListResult",
    "SignupInviteRepository",
    "SignupInviteStatus",
    "SignupInviteReservation",
    "SignupInviteReservationStatus",
    "SignupRequest",
    "SignupRequestCreate",
    "SignupRequestListResult",
    "SignupRequestRepository",
    "SignupRequestStatus",
]
