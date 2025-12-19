"""User consent endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import require_current_user
from app.api.models.common import SuccessNoDataResponse
from app.api.models.consent import ConsentRequest, ConsentView
from app.services.consent_service import ConsentService, get_consent_service

router = APIRouter(prefix="/users", tags=["users"])


def _service() -> ConsentService:
    return get_consent_service()


@router.post(
    "/consents",
    response_model=SuccessNoDataResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_consent(
    payload: ConsentRequest,
    current_user: dict[str, str] = Depends(require_current_user),
) -> SuccessNoDataResponse:
    service = _service()
    await service.record(
        user_id=UUID(current_user["user_id"]),
        policy_key=payload.policy_key,
        version=payload.version,
        ip_hash=payload.ip_hash,
        user_agent_hash=payload.user_agent_hash,
    )
    return SuccessNoDataResponse(message="Consent recorded.")


@router.get("/consents", response_model=list[ConsentView])
async def list_consents(
    current_user: dict[str, str] = Depends(require_current_user),
) -> list[ConsentView]:
    service = _service()
    rows = await service.list_for_user(user_id=UUID(current_user["user_id"]))
    return [
        ConsentView(policy_key=row.policy_key, version=row.version, accepted_at=row.accepted_at)
        for row in rows
    ]
