"""Routes for deterministic test fixture seeding."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
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

