"""Team/member management request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.team import TeamInvite, TeamMember
from app.domain.team_policy import TEAM_INVITE_POLICY
from app.domain.tenant_roles import TenantRole


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    tenant_id: UUID
    email: EmailStr
    display_name: str | None
    role: TenantRole
    status: str
    email_verified: bool
    joined_at: datetime

    @classmethod
    def from_domain(cls, member: TeamMember) -> TeamMemberResponse:
        status = member.status.value if hasattr(member.status, "value") else str(member.status)
        return cls(
            user_id=member.user_id,
            tenant_id=member.tenant_id,
            email=member.email,
            display_name=member.display_name,
            role=member.role,
            status=status,
            email_verified=member.email_verified,
            joined_at=member.joined_at,
        )


class TeamMemberListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[TeamMemberResponse]
    total: int
    owner_count: int


class TeamMemberAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    role: TenantRole


class TeamMemberRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: TenantRole


class TeamInviteIssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invited_email: EmailStr
    role: TenantRole
    expires_in_hours: int | None = Field(
        default=TEAM_INVITE_POLICY.default_expires_hours,
        ge=1,
        le=TEAM_INVITE_POLICY.max_expires_hours,
    )


class TeamInviteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    token_hint: str
    invited_email: EmailStr
    role: TenantRole
    status: str
    created_by_user_id: UUID | None = None
    accepted_by_user_id: UUID | None = None
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    expires_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_domain(cls, invite: TeamInvite) -> TeamInviteResponse:
        status = invite.status.value if hasattr(invite.status, "value") else str(invite.status)
        return cls(
            id=invite.id,
            tenant_id=invite.tenant_id,
            token_hint=invite.token_hint,
            invited_email=invite.invited_email,
            role=invite.role,
            status=status,
            created_by_user_id=invite.created_by_user_id,
            accepted_by_user_id=invite.accepted_by_user_id,
            accepted_at=invite.accepted_at,
            revoked_at=invite.revoked_at,
            revoked_reason=invite.revoked_reason,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
        )


class TeamInviteIssueResponse(TeamInviteResponse):
    invite_token: str = Field(description="Plaintext invite token (only returned once).")


class TeamInviteListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invites: list[TeamInviteResponse]
    total: int


class TeamInviteAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)
    password: str = Field(min_length=14)
    display_name: str | None = Field(default=None, max_length=128)


class TeamInviteAcceptExistingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)


class TeamInvitePolicyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_expires_hours: int
    max_expires_hours: int


__all__ = [
    "TeamInviteAcceptExistingRequest",
    "TeamInviteAcceptRequest",
    "TeamInviteIssueRequest",
    "TeamInviteIssueResponse",
    "TeamInviteListResponse",
    "TeamInvitePolicyResponse",
    "TeamInviteResponse",
    "TeamMemberAddRequest",
    "TeamMemberListResponse",
    "TeamMemberResponse",
    "TeamMemberRoleUpdateRequest",
]
