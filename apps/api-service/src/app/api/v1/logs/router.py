"""Frontend log ingestion endpoint with signed payloads."""

from __future__ import annotations

import hmac
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.core.security import verify_token
from app.core.settings import Settings, get_settings
from app.observability.logging import log_event

router = APIRouter(prefix="/logs", tags=["logs"])

MAX_FIELDS = 32
MAX_BODY_BYTES = 16_384
RESERVED_FIELD_KEYS = {"level", "message"}


class FrontendLogPayload(BaseModel):
    event: str = Field(..., max_length=128)
    scope: str | None = Field(default=None, max_length=64)
    level: str = Field(default="info", max_length=16)
    message: str | None = Field(default=None, max_length=2048)
    timestamp: str | None = Field(default=None, max_length=64)
    fields: dict[str, Any] = Field(default_factory=dict)

    @field_validator("fields", mode="after")
    @classmethod
    def validate_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > MAX_FIELDS:
            raise ValueError(f"fields must have at most {MAX_FIELDS} entries")
        # Strip reserved keys so callers cannot override top-level fields.
        return {k: v for k, v in value.items() if k not in RESERVED_FIELD_KEYS}


class FrontendLogIngestResponse(BaseModel):
    accepted: bool = Field(default=True, description="Whether the log event was accepted.")


def _verify_signature(raw: bytes, signature: str | None, settings: Settings) -> None:
    if not settings.frontend_log_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "Unauthorized",
                "message": "Log signature secret not configured.",
            },
        )
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "Unauthorized",
                "message": "Missing log signature.",
            },
        )
    expected = hmac.new(
        settings.frontend_log_shared_secret.encode(),
        raw,
        sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "Unauthorized",
                "message": "Invalid log signature.",
            },
        )

def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "Unauthorized",
                "message": "Invalid Authorization header.",
            },
        )
    return token.strip()


def _authenticate_frontend_log_request(
    *,
    authorization: str | None,
    raw_body: bytes,
    signature: str | None,
    settings: Settings,
) -> dict[str, Any]:
    """Accept either a valid user access token or a signed anonymous payload."""

    token = _extract_bearer_token(authorization)
    if token:
        payload = verify_token(token, audience=settings.auth_audience)
        if payload.get("token_use") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "Unauthorized",
                    "message": "Access token required.",
                },
            )
        return payload

    if not settings.allow_anon_frontend_logs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "Forbidden",
                "message": "Frontend log ingestion requires authentication.",
            },
        )

    _verify_signature(raw_body, signature, settings)
    return {}


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=FrontendLogIngestResponse,
)
async def ingest_frontend_log(
    request: Request,
    payload: FrontendLogPayload,
    authorization: str | None = Header(None),
    x_log_signature: str | None = Header(None, alias="x-log-signature"),
    settings: Settings = Depends(get_settings),
) -> FrontendLogIngestResponse:
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "PayloadTooLarge",
                "message": "Log payload too large.",
                "details": {"max_bytes": MAX_BODY_BYTES},
            },
        )

    auth_payload = _authenticate_frontend_log_request(
        authorization=authorization,
        raw_body=raw,
        signature=x_log_signature,
        settings=settings,
    )
    user_id = auth_payload.get("sub") if isinstance(auth_payload.get("sub"), str) else None
    if isinstance(user_id, str) and user_id.startswith("user:"):
        user_id = user_id.split("user:", 1)[1]
    else:
        user_id = None

    log_event(
        "frontend.log",
        level=payload.level,
        message=payload.message or payload.event,
        frontend_event=payload.event,
        frontend_scope=payload.scope,
        frontend_timestamp=payload.timestamp,
        frontend_authenticated=bool(user_id),
        frontend_user_id=user_id,
        **payload.fields,
    )

    return FrontendLogIngestResponse(accepted=True)
