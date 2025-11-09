"""Shared helpers for auth API endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status

from app.api.models.auth import (
    SessionClientInfo,
    SessionLocationInfo,
    UserSessionItem,
    UserSessionResponse,
)
from app.domain.auth import UserSession, UserSessionTokens
from app.services.auth_service import UserAuthenticationError
from app.services.user_service import (
    InvalidCredentialsError,
    IpThrottledError,
    TenantContextRequiredError,
    UserDisabledError,
    UserLockedError,
)


def extract_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or None
    if request.client and request.client.host:
        return request.client.host
    return None


def extract_user_agent(request: Request) -> str | None:
    header = request.headers.get("user-agent")
    return header.strip() if header else None


def to_user_session_response(tokens: UserSessionTokens) -> UserSessionResponse:
    return UserSessionResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_at=tokens.expires_at,
        refresh_expires_at=tokens.refresh_expires_at,
        kid=tokens.kid,
        refresh_kid=tokens.refresh_kid,
        scopes=tokens.scopes,
        tenant_id=tokens.tenant_id,
        user_id=tokens.user_id,
        email_verified=tokens.email_verified,
        session_id=UUID(tokens.session_id),
    )


def current_session_uuid(user: dict[str, Any]) -> UUID | None:
    payload = user.get("payload") if isinstance(user, dict) else None
    if not isinstance(payload, dict):
        return None
    sid = payload.get("sid")
    if not isinstance(sid, str):
        return None
    try:
        return UUID(sid)
    except ValueError:  # pragma: no cover - defensive
        return None


def to_session_item(session: UserSession, current_session_id: UUID | None) -> UserSessionItem:
    location = (
        SessionLocationInfo(
            city=session.location.city,
            region=session.location.region,
            country=session.location.country,
        )
        if session.location
        else None
    )
    client = SessionClientInfo(
        platform=session.client.platform,
        browser=session.client.browser,
        device=session.client.device,
        user_agent=session.user_agent,
    )
    return UserSessionItem(
        id=session.id,
        tenant_id=session.tenant_id,
        created_at=session.created_at,
        last_seen_at=session.last_seen_at,
        revoked_at=session.revoked_at,
        ip_address_masked=session.ip_masked,
        fingerprint=session.fingerprint,
        client=client,
        location=location,
        current=current_session_id == session.id if current_session_id else False,
    )


def map_user_auth_error(exc: UserAuthenticationError) -> HTTPException:
    cause = exc.__cause__
    if isinstance(cause, InvalidCredentialsError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(cause),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(cause, UserLockedError):
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(cause))
    if isinstance(cause, UserDisabledError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(cause))
    if isinstance(cause, TenantContextRequiredError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(cause))
    if isinstance(cause, IpThrottledError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(cause),
        )
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )
