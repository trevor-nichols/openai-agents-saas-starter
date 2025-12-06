"""Shared dependency utilities for API routers."""

from fastapi import Query

from app.api.models.common import PaginationParams


def pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)."),
    limit: int = Query(20, ge=1, le=100, description="Page size."),
) -> PaginationParams:
    """Return validated pagination parameters."""

    return PaginationParams(page=page, limit=limit)
