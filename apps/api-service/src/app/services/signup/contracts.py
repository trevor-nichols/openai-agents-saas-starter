"""Shared data structures for signup orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.auth_service import UserSessionTokens


@dataclass(slots=True)
class SignupCommand:
    email: str
    password: str
    tenant_name: str
    display_name: str | None
    plan_code: str | None
    trial_days: int | None
    ip_address: str | None
    user_agent: str | None
    invite_token: str | None


@dataclass(slots=True)
class SignupResult:
    tenant_id: str
    tenant_slug: str
    user_id: str
    session: UserSessionTokens


__all__ = ["SignupCommand", "SignupResult"]
