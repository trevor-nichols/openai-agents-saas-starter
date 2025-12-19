"""Asset catalog endpoints for generated files and images."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.assets.schemas import (
    AssetDownloadResponse,
    AssetListResponse,
    AssetResponse,
    AssetSourceTool,
    AssetType,
)
from app.bootstrap.container import get_container, wire_asset_service
from app.domain.assets import AssetNotFoundError
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid as coerce_conversation_uuid_from_persistence,
)
from app.services.assets.service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])


def _svc() -> AssetService:
    container = get_container()
    if container.asset_service is None:
        wire_asset_service(container)
    if container.asset_service is None:
        raise RuntimeError("AssetService is not configured")
    return container.asset_service


def _uuid(value: str | uuid.UUID) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # pragma: no cover - FastAPI validation should catch
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID",
        ) from exc


def _asset_response(view) -> AssetResponse:
    asset = view.asset
    return AssetResponse(
        id=asset.id,
        storage_object_id=asset.storage_object_id,
        asset_type=asset.asset_type,
        source_tool=asset.source_tool,
        conversation_id=asset.conversation_id,
        message_id=asset.message_id,
        tool_call_id=asset.tool_call_id,
        response_id=asset.response_id,
        container_id=asset.container_id,
        openai_file_id=asset.openai_file_id,
        metadata=asset.metadata,
        filename=view.filename,
        mime_type=view.mime_type,
        size_bytes=view.size_bytes,
        agent_key=view.agent_key,
        storage_status=view.storage_status,
        asset_created_at=asset.created_at,
        asset_updated_at=asset.updated_at,
        storage_created_at=view.storage_created_at,
    )


@router.get("", response_model=AssetListResponse)
async def list_assets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    asset_type: AssetType | None = Query(default=None),
    source_tool: AssetSourceTool | None = Query(default=None),
    conversation_id: str | None = Query(default=None),
    message_id: int | None = Query(default=None, ge=1),
    agent_key: str | None = Query(default=None, max_length=64),
    mime_type_prefix: str | None = Query(default=None, max_length=64),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: AssetService = Depends(_svc),
) -> AssetListResponse:
    conversation_uuid = (
        coerce_conversation_uuid_from_persistence(conversation_id)
        if conversation_id
        else None
    )
    items = await service.list_assets(
        tenant_id=_uuid(tenant_context.tenant_id),
        limit=limit,
        offset=offset,
        asset_type=asset_type,
        source_tool=source_tool,
        conversation_id=conversation_uuid,
        message_id=message_id,
        agent_key=agent_key,
        mime_type_prefix=mime_type_prefix,
        created_after=created_after,
        created_before=created_before,
    )
    next_offset = offset + limit if len(items) == limit else None
    return AssetListResponse(
        items=[_asset_response(view) for view in items],
        next_offset=next_offset,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: uuid.UUID,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: AssetService = Depends(_svc),
) -> AssetResponse:
    try:
        asset = await service.get_asset(
            tenant_id=_uuid(tenant_context.tenant_id),
            asset_id=_uuid(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _asset_response(asset)


@router.get("/{asset_id}/download-url", response_model=AssetDownloadResponse)
async def get_asset_download_url(
    asset_id: uuid.UUID,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: AssetService = Depends(_svc),
) -> AssetDownloadResponse:
    try:
        presign, storage_obj = await service.get_download_url(
            tenant_id=_uuid(tenant_context.tenant_id),
            asset_id=_uuid(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if storage_obj.id is None:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage object metadata missing",
        )
    ttl = service.signed_url_ttl()
    return AssetDownloadResponse(
        asset_id=_uuid(asset_id),
        storage_object_id=storage_obj.id,
        download_url=presign.url,
        method=presign.method,
        headers=presign.headers,
        expires_in_seconds=ttl,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: uuid.UUID,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)
    ),
    service: AssetService = Depends(_svc),
):
    try:
        await service.delete_asset(
            tenant_id=_uuid(tenant_context.tenant_id),
            asset_id=_uuid(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
