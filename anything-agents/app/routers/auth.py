# File: app/routers/auth.py
# Purpose: Authentication endpoints for anything-agents
# Dependencies: fastapi, app/schemas/auth, app/core/security
# Used by: Frontend applications for user authentication

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import Token, UserLogin
from app.schemas.common import SuccessResponse
from app.core.security import create_access_token, get_current_user
from app.core.config import get_settings

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(user_credentials: UserLogin):
    """
    Authenticate user and return JWT access token.
    
    This is a demo endpoint. In a real application, you would:
    1. Validate credentials against a user database
    2. Check if user is active
    3. Return appropriate error messages
    """
    settings = get_settings()
    
    # Demo authentication - replace with real user validation
    if user_credentials.username == "demo" and user_credentials.password == "demo123":
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": "demo_user_id", "username": user_credentials.username},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(current_user: dict = Depends(get_current_user)):
    """Refresh the access token for the current user."""
    settings = get_settings()
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user["user_id"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return SuccessResponse(
        message="User information retrieved successfully",
        data={
            "user_id": current_user["user_id"],
            "token_payload": current_user["payload"]
        }
    ) 