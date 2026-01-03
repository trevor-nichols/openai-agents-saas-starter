"""Health and readiness endpoints surfaced at the root of the service."""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.api.models.common import HealthFeaturesResponse, HealthResponse
from app.bootstrap.container import get_container, wire_storage_service
from app.core.settings import get_settings
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


@router.get("/health/features", response_model=HealthFeaturesResponse)
async def feature_flags() -> HealthFeaturesResponse:
    """Expose backend feature flags for downstream clients."""

    settings = get_settings()
    billing_enabled = settings.enable_billing
    billing_stream_enabled = bool(settings.enable_billing_stream and billing_enabled)
    return HealthFeaturesResponse(
        billing_enabled=billing_enabled,
        billing_stream_enabled=billing_stream_enabled,
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


@router.get("/health/storage", response_model=HealthResponse)
async def storage_health() -> HealthResponse:
    """Storage provider health (informational; does not gate readiness)."""

    settings = get_settings()
    container = get_container()
    if container.storage_service is None:
        try:
            wire_storage_service(container)
        except Exception:
            return HealthResponse(
                status="unconfigured",
                timestamp=datetime.utcnow().isoformat(),
                version=settings.app_version,
                uptime=round(time.time() - _start_time, 2),
            )
    if container.storage_service is None:
        return HealthResponse(
            status="unconfigured",
            timestamp=datetime.utcnow().isoformat(),
            version=settings.app_version,
            uptime=round(time.time() - _start_time, 2),
        )

    status_detail = await container.storage_service.health_check()
    return HealthResponse(
        status=status_detail.get("status", "unknown"),
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - _start_time, 2),
    )
