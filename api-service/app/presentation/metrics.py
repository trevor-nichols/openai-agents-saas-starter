"""Prometheus scrape endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.observability.metrics import REGISTRY

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    payload = generate_latest(REGISTRY)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
