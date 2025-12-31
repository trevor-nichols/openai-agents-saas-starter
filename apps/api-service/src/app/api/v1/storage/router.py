"""Tenant-scoped storage endpoints (presigned upload/download, list, delete)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.storage.schemas import (
    StorageObjectListResponse,
    StorageObjectResponse,
    StoragePresignDownloadResponse,
    StoragePresignUploadRequest,
    StoragePresignUploadResponse,
)
from app.bootstrap.container import get_container, wire_storage_service
from app.services.storage.service import PresignedUpload, StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


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


def _download_response(
    object_id: uuid.UUID, presign, ttl: int
) -> StoragePresignDownloadResponse:
    return StoragePresignDownloadResponse(
        object_id=object_id,
        download_url=presign.url,
        method=presign.method,
        headers=presign.headers,
        bucket="",  # set by router with bucket
        object_key="",  # set by router with key
        expires_in_seconds=ttl,
    )


def _object_response(obj) -> StorageObjectResponse:
    return StorageObjectResponse(
        id=obj.id,
        bucket=obj.bucket,
        object_key=obj.key,
        filename=obj.filename,
        mime_type=obj.mime_type,
        size_bytes=obj.size_bytes,
        status=obj.status,
        created_at=obj.created_at,
        conversation_id=obj.conversation_id,
        agent_key=obj.agent_key,
    )


@router.post(
    "/objects/upload-url",
    response_model=StoragePresignUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_presigned_upload(
    payload: StoragePresignUploadRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: StorageService = Depends(_svc),
):
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
    user_uuid = _uuid(user_id) if user_id else None
    try:
        presign = await service.create_presigned_upload(
            tenant_id=_uuid(tenant_context.tenant_id),
            user_id=user_uuid,
            filename=payload.filename,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            agent_key=payload.agent_key,
            conversation_id=payload.conversation_id,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    ttl = service.signed_url_ttl()
    return _upload_response(presign, ttl)


@router.get("/objects", response_model=StorageObjectListResponse)
async def list_objects(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conversation_id: uuid.UUID | None = Query(default=None),
    tenant_context: TenantContext = Depends(
        require_tenant_role(
            TenantRole.VIEWER,
            TenantRole.MEMBER,
            TenantRole.ADMIN,
            TenantRole.OWNER,
        )
    ),
    service: StorageService = Depends(_svc),
):
    items = await service.list_objects(
        tenant_id=_uuid(tenant_context.tenant_id),
        limit=limit,
        offset=offset,
        conversation_id=conversation_id,
    )
    next_offset = offset + limit if len(items) == limit else None
    return StorageObjectListResponse(
        items=[_object_response(obj) for obj in items],
        next_offset=next_offset,
    )


@router.get(
    "/objects/{object_id}/download-url",
    response_model=StoragePresignDownloadResponse,
)
async def get_download_url(
    object_id: uuid.UUID,
    tenant_context: TenantContext = Depends(
        require_tenant_role(
            TenantRole.VIEWER,
            TenantRole.MEMBER,
            TenantRole.ADMIN,
            TenantRole.OWNER,
        )
    ),
    service: StorageService = Depends(_svc),
):
    try:
        presign, obj = await service.get_presigned_download(
            tenant_id=_uuid(tenant_context.tenant_id),
            object_id=_uuid(object_id),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    ttl = service.signed_url_ttl()
    return StoragePresignDownloadResponse(
        object_id=_uuid(object_id),
        download_url=presign.url,
        method=presign.method,
        headers=presign.headers,
        bucket=obj.bucket,
        object_key=obj.key,
        expires_in_seconds=ttl,
    )


@router.delete(
    "/objects/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_object(
    object_id: uuid.UUID,
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: StorageService = Depends(_svc),
):
    await service.delete_object(
        tenant_id=_uuid(tenant_context.tenant_id),
        object_id=_uuid(object_id),
    )
    return None
