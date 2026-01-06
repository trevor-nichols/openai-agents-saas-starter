"""Tenant settings endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.tenant_settings import TenantSettingsResponse, TenantSettingsUpdateRequest
from app.domain.tenant_settings import TenantSettingsConflictError
from app.services.tenant import tenant_settings_service as tenant_settings_module
from app.services.tenant.tenant_settings_service import TenantSettingsValidationError

router = APIRouter()


@router.get("/settings", response_model=TenantSettingsResponse)
async def get_tenant_settings(
    response: Response,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
) -> TenantSettingsResponse:
    service = tenant_settings_module.get_tenant_settings_service()
    snapshot = await service.get_settings(context.tenant_id)
    response.headers["ETag"] = _format_version_etag(snapshot.version)
    return TenantSettingsResponse.from_snapshot(snapshot)


@router.put("/settings", response_model=TenantSettingsResponse)
async def update_tenant_settings(
    response: Response,
    payload: TenantSettingsUpdateRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
    if_match: str | None = Header(None, alias="If-Match"),
) -> TenantSettingsResponse:
    expected_version = _parse_if_match(if_match)
    mapped = payload.dict_for_service()
    service = tenant_settings_module.get_tenant_settings_service()
    try:
        snapshot = await service.update_settings(
            context.tenant_id,
            billing_contacts=mapped["billing_contacts"],
            billing_webhook_url=mapped["billing_webhook_url"],
            plan_metadata=mapped["plan_metadata"],
            flags=mapped["flags"],
            expected_version=expected_version,
        )
    except TenantSettingsValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TenantSettingsConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    response.headers["ETag"] = _format_version_etag(snapshot.version)
    return TenantSettingsResponse.from_snapshot(snapshot)


def _format_version_etag(version: int) -> str:
    return f'"{version}"'


def _parse_if_match(value: str | None) -> int:
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Missing If-Match header with tenant settings version.",
        )
    candidate = value.strip()
    if candidate.startswith("W/"):
        candidate = candidate[2:].strip()
    if candidate.startswith('"') and candidate.endswith('"') and len(candidate) >= 2:
        candidate = candidate[1:-1]
    if candidate == "*":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='If-Match must specify a concrete version (e.g. "3").',
        )
    try:
        parsed = int(candidate)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='If-Match must be an integer version (e.g. "3").',
        ) from exc
    if parsed < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match version must be non-negative.",
        )
    return parsed
