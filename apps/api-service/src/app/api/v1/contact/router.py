"""Public contact form endpoint."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.models.common import SuccessResponse
from app.api.models.contact import ContactSubmissionRequest, ContactSubmissionResponse
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent
from app.core.config import get_settings
from app.services.contact_service import (
    ContactDeliveryError,
    ContactSubmissionError,
    get_contact_service,
)
from app.services.shared.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter

router = APIRouter(tags=["contact"])


@router.post(
    "/contact",
    response_model=SuccessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_contact(payload: ContactSubmissionRequest, request: Request) -> SuccessResponse:
    client_ip = extract_client_ip(request)
    await _enforce_contact_quota(payload.email, client_ip)

    service = get_contact_service()
    try:
        result = await service.submit_contact(
            name=payload.name,
            email=payload.email,
            company=payload.company,
            topic=payload.topic,
            message=payload.message,
            ip_address=client_ip,
            user_agent=extract_user_agent(request),
            honeypot=payload.honeypot,
        )
    except ContactDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to deliver your message right now. Please try again shortly.",
        ) from exc
    except ContactSubmissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    response = ContactSubmissionResponse.model_validate(asdict(result))
    return SuccessResponse(
        message="Thanks for reaching out. We'll respond soon.",
        data=response,
    )


async def _enforce_contact_quota(email: str, client_ip: str | None) -> None:
    settings = get_settings()
    quotas: list[tuple[RateLimitQuota, list[str]]] = []

    per_email = settings.contact_email_rate_limit_per_email_per_hour
    if per_email > 0:
        quotas.append(
            (
                RateLimitQuota(
                    name="contact_email",
                    limit=per_email,
                    window_seconds=3600,
                    scope="email",
                ),
                [email.lower()],
            )
        )

    per_ip = settings.contact_email_rate_limit_per_ip_per_hour
    if per_ip > 0 and client_ip:
        quotas.append(
            (
                RateLimitQuota(
                    name="contact_ip",
                    limit=per_ip,
                    window_seconds=3600,
                    scope="ip",
                ),
                [client_ip],
            )
        )

    for quota, keys in quotas:
        try:
            await rate_limiter.enforce(quota, keys)
        except RateLimitExceeded as exc:
            raise_rate_limit_http_error(exc, tenant_id="contact", user_id=keys[0])
