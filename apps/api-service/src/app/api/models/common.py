"""Common API response and pagination models."""

from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Standard success response envelope."""

    success: bool = Field(
        default=True,
        description="Operation success status flag.",
    )
    message: str = Field(description="Human-readable summary of the result.")
    data: Any | None = Field(
        default=None,
        description="Optional payload containing the result.",
    )


class SuccessNoDataResponse(SuccessResponse):
    """Success response where `data` is always null."""

    data: None = Field(
        default=None,
        description="Always null for this response type.",
    )


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = Field(
        default=False,
        description="Operation success status flag.",
    )
    error: str = Field(description="Short machine-readable error name.")
    message: str = Field(description="Human-readable error description.")
    details: Any | None = Field(
        default=None,
        description="Additional error context for debugging.",
    )


class ValidationErrorResponse(BaseModel):
    """Validation error envelope for request/response parsing errors (422)."""

    success: bool = Field(
        default=False,
        description="Operation success status flag.",
    )
    error: str = Field(default="ValidationError", description="Short machine-readable error name.")
    message: str = Field(
        default="Request validation failed.",
        description="Human-readable error description.",
    )
    details: list[dict[str, Any]] = Field(
        description="Pydantic validation errors list.",
    )


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(description="Service health status.")
    timestamp: str = Field(description="ISO-8601 timestamp of the probe.")
    version: str = Field(description="Semantic version of the service.")
    uptime: float | None = Field(
        default=None,
        description="Process uptime in seconds when available.",
    )


class PaginationParams(BaseModel):
    """Common pagination request parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum items to return.",
    )


class PaginatedResponse(BaseModel):
    """Standard pagination metadata."""

    items: list[Any] = Field(description="Returned items.")
    total: int = Field(description="Total available items.")
    page: int = Field(description="Current page number.")
    limit: int = Field(description="Requested items per page.")
    pages: int = Field(description="Total number of pages.")
    has_next: bool = Field(description="Whether a subsequent page exists.")
    has_prev: bool = Field(description="Whether a previous page exists.")
