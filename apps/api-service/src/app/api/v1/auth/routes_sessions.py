"""Session-focused auth endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies.auth import require_current_user
from app.api.models.auth import (
    UserLoginRequest,
    UserLogoutRequest,
    UserRefreshRequest,
    UserSessionListResponse,
    UserSessionResponse,
)
from app.api.models.common import SuccessResponse
from app.api.v1.auth.utils import (
    current_session_uuid,
    extract_client_ip,
    extract_user_agent,
    map_user_auth_error,
    to_session_item,
    to_user_session_response,
)
from app.services.auth_service import (
    UserAuthenticationError,
    UserLogoutError,
    UserRefreshError,
    auth_service,
)
from app.services.users import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    UserDisabledError,
    UserLockedError,
)

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=UserSessionResponse)
async def login_for_access_token(
    payload: UserLoginRequest,
    request: Request,
) -> UserSessionResponse:
    """Authenticate a user and mint fresh access/refresh tokens."""

    client_ip = extract_client_ip(request)
    user_agent = extract_user_agent(request)

    try:
        tokens = await auth_service.login_user(
            email=payload.email,
            password=payload.password,
            tenant_id=payload.tenant_id or None,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except UserAuthenticationError as exc:
        raise map_user_auth_error(exc) from exc

    return to_user_session_response(tokens)


@router.post("/refresh", response_model=UserSessionResponse)
async def refresh_access_token(
    payload: UserRefreshRequest,
    request: Request,
) -> UserSessionResponse:
    """Exchange a refresh token for a new access/refresh pair."""

    client_ip = extract_client_ip(request)
    user_agent = extract_user_agent(request)

    try:
        tokens = await auth_service.refresh_user_session(
            payload.refresh_token,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except (InvalidCredentialsError, MembershipNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserRefreshError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserLockedError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except UserDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return to_user_session_response(tokens)


@router.post("/logout", response_model=SuccessResponse)
async def logout_session(
    payload: UserLogoutRequest,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> SuccessResponse:
    """Revoke a single refresh token for the authenticated user."""

    try:
        revoked = await auth_service.logout_user_session(
            refresh_token=payload.refresh_token,
            expected_user_id=current_user["user_id"],
        )
    except UserLogoutError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UserRefreshError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    message = "Session revoked successfully." if revoked else "Session already inactive."
    return SuccessResponse(message=message, data={"revoked": revoked})


@router.post("/logout/all", response_model=SuccessResponse)
async def logout_all_sessions(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> SuccessResponse:
    """Revoke every refresh token tied to the authenticated user."""

    user_uuid = UUID(current_user["user_id"])
    revoked = await auth_service.revoke_user_sessions(user_uuid, reason="user_logout_all")
    message = "All sessions revoked successfully." if revoked else "No active sessions to revoke."
    return SuccessResponse(message=message, data={"revoked": revoked})


@router.get("/sessions", response_model=UserSessionListResponse)
async def list_user_sessions(
    include_revoked: bool = Query(
        default=False,
        description="When true, include revoked sessions in the response.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of sessions to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset applied when listing sessions.",
    ),
    tenant_id: UUID | None = Query(
        default=None,
        description="Optional tenant scope for filtering sessions.",
    ),
    current_user: dict[str, Any] = Depends(require_current_user),
) -> UserSessionListResponse:
    """Return paginated session/device metadata for the authenticated user."""

    user_uuid = UUID(current_user["user_id"])
    current_session = current_session_uuid(current_user)
    try:
        result = await auth_service.list_user_sessions(
            user_id=user_uuid,
            tenant_id=tenant_id,
            include_revoked=include_revoked,
            limit=limit,
            offset=offset,
        )
    except RuntimeError as exc:  # pragma: no cover - misconfiguration
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    sessions = [to_session_item(entry, current_session) for entry in result.sessions]
    return UserSessionListResponse(
        sessions=sessions,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def revoke_user_session(
    session_id: UUID,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> SuccessResponse:
    """Revoke a specific session/device for the authenticated user."""

    user_uuid = UUID(current_user["user_id"])
    try:
        revoked = await auth_service.revoke_user_session_by_id(
            user_id=user_uuid,
            session_id=session_id,
            reason="user_session_manual_revoke",
        )
    except RuntimeError as exc:  # pragma: no cover - misconfiguration
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked.",
        )
    return SuccessResponse(message="Session revoked successfully.", data={"revoked": True})


@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> SuccessResponse:
    """Return metadata about the current authenticated user."""

    return SuccessResponse(
        message="User information retrieved successfully",
        data={
            "user_id": current_user["user_id"],
            "token_payload": current_user["payload"],
        },
    )
