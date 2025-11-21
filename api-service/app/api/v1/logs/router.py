"""Frontend log ingest endpoint (feature-gated)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.api.dependencies.auth import CurrentUser, require_current_user
from app.api.dependencies.rate_limit import raise_rate_limit_http_error
from app.observability.logging import log_event
from app.services.shared.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter

router = APIRouter(prefix="/logs", tags=["observability"])

LOG_INGEST_QUOTA = RateLimitQuota(
    name="frontend_log_ingest.per_minute", limit=60, window_seconds=60, scope="user"
)
MAX_BODY_BYTES = 16_384
MAX_FIELDS = 50
_RESERVED_FIELDS = {
    "level",
    "message",
    "event",
    "tenant_id",
    "user_id",
    "frontend_event",
    "source",
    "fields",
}


class FrontendLogPayload(BaseModel):
    event: str = Field(
        ...,
        max_length=128,
        description="Logical event name from the frontend logger.",
    )
    level: Literal["debug", "info", "warn", "error"] = Field(
        default="info", description="Severity level from the frontend logger."
    )
    message: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional human-readable message; falls back to event when absent.",
    )
    fields: dict[str, Any] | None = Field(
        default=None,
        description="Structured context payload; keys must be JSON-serializable strings.",
    )
    source: str | None = Field(
        default="frontend",
        max_length=32,
        description="Source tag (e.g., web-app, marketing-site).",
    )

    @field_validator("fields")
    @classmethod
    def limit_fields(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        if len(value) > MAX_FIELDS:
            raise ValueError(f"Too many fields; maximum {MAX_FIELDS}.")
        for key in value.keys():
            if not isinstance(key, str):
                raise ValueError("Field keys must be strings.")
        return value


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_frontend_log(
    request: Request,
    current_user: CurrentUser = Depends(require_current_user),
) -> dict[str, bool]:
    payload = await _parse_payload_with_limit(request)

    tenant_id = str(
        current_user.get("tenant_id")
        or current_user.get("payload", {}).get("tenant_id")
        or "unknown"
    )
    user_id = str(
        current_user.get("sub")
        or current_user.get("user_id")
        or current_user.get("id")
        or "unknown"
    )

    try:
        await rate_limiter.enforce(LOG_INGEST_QUOTA, [tenant_id, user_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=user_id)

    sanitized_fields = {
        key: value for key, value in (payload.fields or {}).items() if key not in _RESERVED_FIELDS
    }

    log_event(
        "frontend.log",
        level=payload.level,
        message=payload.message or payload.event,
        tenant_id=tenant_id,
        user_id=user_id,
        frontend_event=payload.event,
        source=payload.source or "frontend",
        **sanitized_fields,
    )

    return {"accepted": True}


async def _parse_payload_with_limit(request: Request) -> FrontendLogPayload:
    size = 0
    chunks: list[bytes] = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_BODY_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Log payload too large.",
            )
        chunks.append(chunk)

    body = b"".join(chunks)
    try:
        return FrontendLogPayload.model_validate_json(body or b"{}")
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
