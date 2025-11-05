"""Health and readiness endpoints surfaced at the root of the service."""

import time
from datetime import datetime

from fastapi import APIRouter

from app.api.models.common import HealthResponse
from app.core.config import get_settings

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
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - _start_time, 2),
    )
