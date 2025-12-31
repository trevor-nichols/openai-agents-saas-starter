"""Upload endpoints for agent input attachments."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.storage.schemas import StoragePresignUploadRequest, StoragePresignUploadResponse
from app.bootstrap.container import get_container, wire_storage_service
from app.services.storage.service import PresignedUpload, StorageService

router = APIRouter(prefix="/uploads", tags=["uploads"])


_ALLOWED_VIEWER_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.MEMBER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


def _svc() -> StorageService:
    container = get_container()
    if container.storage_service is None:
        wire_storage_service(container)
    if container.storage_service is None:
        raise RuntimeError("StorageService is not configured")
    return container.storage_service


def _uuid(value: str | uuid.UUID) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # pragma: no cover - FastAPI validation should catch
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID",
        ) from exc


def _upload_response(resp: PresignedUpload, ttl: int) -> StoragePresignUploadResponse:
    return StoragePresignUploadResponse(
        object_id=resp.object_id,
        upload_url=resp.upload_url,
        method=resp.method,
        headers=resp.headers,
        bucket=resp.bucket,
        object_key=resp.object_key,
        expires_in_seconds=ttl,
    )


@router.post(
    "/agent-input",
    response_model=StoragePresignUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_input_upload(
    payload: StoragePresignUploadRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
    service: StorageService = Depends(_svc),
) -> StoragePresignUploadResponse:
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
    user_uuid = _uuid(user_id) if user_id else None
    metadata = {**(payload.metadata or {}), "source": "user_upload", "purpose": "agent_input"}
    try:
        presign = await service.create_presigned_upload(
            tenant_id=_uuid(tenant_context.tenant_id),
            user_id=user_uuid,
            filename=payload.filename,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            agent_key=payload.agent_key,
            conversation_id=payload.conversation_id,
            metadata=metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    ttl = service.signed_url_ttl()
    return _upload_response(presign, ttl)
