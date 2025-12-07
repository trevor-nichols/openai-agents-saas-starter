"""Pydantic models for MFA endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TotpEnrollResponse(BaseModel):
    secret: str
    method_id: UUID
    otpauth_url: str | None = None


class TotpVerifyRequest(BaseModel):
    method_id: UUID
    code: str = Field(..., min_length=6, max_length=8)


class MfaMethodView(BaseModel):
    id: UUID
    method_type: str
    label: str | None = None
    verified_at: str | None = None
    last_used_at: str | None = None
    revoked_at: str | None = None


class RecoveryCodesResponse(BaseModel):
    codes: list[str]


class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str
    methods: list[MfaMethodView]


class MfaChallengeCompleteRequest(BaseModel):
    challenge_token: str = Field(..., min_length=10)
    method_id: UUID
    code: str = Field(..., min_length=6, max_length=8)
