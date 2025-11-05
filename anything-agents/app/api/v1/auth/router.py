"""Authentication endpoints for API v1."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_current_user
from app.api.models.auth import Token, UserLogin
from app.api.models.common import SuccessResponse
from app.core.config import get_settings
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: UserLogin) -> Token:
    """Authenticate a demo user and return a bearer token."""

    settings = get_settings()

    if credentials.username == "demo" and credentials.password == "demo123":
        expiry = timedelta(minutes=settings.access_token_expire_minutes)
        token = create_access_token(
            data={"sub": "demo_user_id", "username": credentials.username},
            expires_delta=expiry,
        )
        return Token(access_token=token, expires_in=int(expiry.total_seconds()))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(current_user: dict = Depends(require_current_user)) -> Token:
    """Issue a fresh token for the current authenticated user."""

    settings = get_settings()
    expiry = timedelta(minutes=settings.access_token_expire_minutes)

    token = create_access_token(
        data={"sub": current_user["user_id"]},
        expires_delta=expiry,
    )
    return Token(access_token=token, expires_in=int(expiry.total_seconds()))


@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(
    current_user: dict = Depends(require_current_user),
) -> SuccessResponse:
    """Return metadata about the current authenticated user."""

    return SuccessResponse(
        message="User information retrieved successfully",
        data={
            "user_id": current_user["user_id"],
            "token_payload": current_user["payload"],
        },
    )
