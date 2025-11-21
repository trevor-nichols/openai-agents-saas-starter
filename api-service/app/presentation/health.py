"""Health and readiness endpoints surfaced at the root of the service."""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.api.models.common import HealthResponse
from app.core.config import get_settings
from app.infrastructure.db import verify_database_connection

router = APIRouter()
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness probe."""

    settings = get_settings()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - _start_time, 2),
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness probe for orchestrators (extend with dependency checks)."""

    settings = get_settings()
    try:
        await verify_database_connection()
    except Exception as exc:  # pragma: no cover - readiness failure
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity check failed: {exc}",
        ) from exc

    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - _start_time, 2),
    )
