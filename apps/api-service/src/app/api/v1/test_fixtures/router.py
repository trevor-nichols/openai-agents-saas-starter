"""Routes for deterministic test fixture seeding."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.settings import Settings, get_settings
from app.services.signup.email_verification_service import (
    EmailVerificationError,
    EmailVerificationTokenIssueResult,
    get_email_verification_service,
)
from app.services.test_fixtures import (
    FixtureApplyResult,
    PlaywrightFixtureSpec,
    TestFixtureError,
    TestFixtureService,
)

router = APIRouter(prefix="/test-fixtures", tags=["test-fixtures"])


def require_test_fixture_mode(settings: Settings = Depends(get_settings)) -> Settings:
    if not settings.use_test_fixtures:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return settings


@router.post(
    "/apply",
    response_model=FixtureApplyResult,
    status_code=status.HTTP_201_CREATED,
)
async def apply_test_fixtures(
    spec: PlaywrightFixtureSpec,
    _settings: Settings = Depends(require_test_fixture_mode),
) -> FixtureApplyResult:
    service = TestFixtureService()
    try:
        return await service.apply_spec(spec)
    except TestFixtureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


class EmailVerificationTokenRequest(BaseModel):
    email: EmailStr
    ip_address: str | None = None
    user_agent: str | None = None


class EmailVerificationTokenResponse(BaseModel):
    token: str
    user_id: str
    expires_at: datetime


@router.post(
    "/email-verification-token",
    response_model=EmailVerificationTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_email_verification_token(
    payload: EmailVerificationTokenRequest,
    _settings: Settings = Depends(require_test_fixture_mode),
) -> EmailVerificationTokenResponse:
    service = get_email_verification_service()
    try:
        result: EmailVerificationTokenIssueResult = await service.issue_token_for_testing(
            email=payload.email,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
        )
    except EmailVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return EmailVerificationTokenResponse(
        token=result.token,
        user_id=str(result.user_id),
        expires_at=result.expires_at,
    )
