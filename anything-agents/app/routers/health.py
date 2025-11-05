# File: app/routers/health.py
# Purpose: Health check endpoints for anything-agents
# Dependencies: fastapi, app/schemas/common
# Used by: Load balancers and monitoring systems

import time
from datetime import datetime
from fastapi import APIRouter
from app.schemas.common import HealthResponse
from app.core.config import get_settings

router = APIRouter()
start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - start_time, 2)
    )

@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check for Kubernetes deployment."""
    settings = get_settings()
    
    # Add your readiness checks here (database, external services, etc.)
    # For now, we'll just return healthy
    
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        uptime=round(time.time() - start_time, 2)
    ) 