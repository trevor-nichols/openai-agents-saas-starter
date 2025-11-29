"""Tenant-scoped container CRUD and agent binding endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.v1.containers.deps import tenant_admin, tenant_viewer
from app.api.v1.containers.schemas import (
    ContainerBindRequest,
    ContainerCreateRequest,
    ContainerListResponse,
    ContainerResponse,
)
from app.bootstrap.container import get_container, wire_container_service
from app.services.containers import (
    ContainerNameConflictError,
    ContainerNotFoundError,
    ContainerQuotaError,
    ContainerService,
)

router = APIRouter(prefix="/containers", tags=["containers"])


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID"
        ) from exc


def _svc() -> ContainerService:
    container = get_container()
    if container.container_service is None:
        wire_container_service(container)
    if container.container_service is None:
        raise RuntimeError("ContainerService is not configured")
    return container.container_service


def _response(model) -> ContainerResponse:
    return ContainerResponse(
        id=model.id,
        openai_id=model.openai_id,
        tenant_id=model.tenant_id,
        owner_user_id=model.owner_user_id,
        name=model.name,
        memory_limit=model.memory_limit,
        status=model.status,
        expires_after=model.expires_after,
        last_active_at=model.last_active_at,
        metadata=model.metadata_json or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.post("", response_model=ContainerResponse, status_code=status.HTTP_201_CREATED)
async def create_container(
    payload: ContainerCreateRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: ContainerService = Depends(_svc),
) -> ContainerResponse:
    owner_user = current_user.get("user_id") if isinstance(current_user, dict) else None
    owner_uuid = _uuid(owner_user) if owner_user else None
    try:
        container = await service.create_container(
            tenant_id=_uuid(tenant_context.tenant_id),
            owner_user_id=owner_uuid,
            name=payload.name,
            memory_limit=payload.memory_limit,
            expires_after=payload.expires_after,
            file_ids=payload.file_ids,
            metadata=payload.metadata,
        )
    except ContainerQuotaError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ContainerNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _response(container)


@router.get("", response_model=ContainerListResponse)
async def list_containers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: ContainerService = Depends(_svc),
) -> ContainerListResponse:
    containers, total = await service.list_containers(
        tenant_id=_uuid(tenant_context.tenant_id), limit=limit, offset=offset
    )
    return ContainerListResponse(items=[_response(c) for c in containers], total=total)


@router.get("/{container_id}", response_model=ContainerResponse)
async def get_container_by_id(
    container_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: ContainerService = Depends(_svc),
) -> ContainerResponse:
    try:
        container = await service.get_container(
            container_id=container_id, tenant_id=_uuid(tenant_context.tenant_id)
        )
    except ContainerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Container not found"
        ) from None
    return _response(container)


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_container(
    container_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: ContainerService = Depends(_svc),
):
    try:
        await service.delete_container(
            container_id=container_id, tenant_id=_uuid(tenant_context.tenant_id)
        )
    except ContainerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Container not found"
        ) from None
    return None


@router.post(
    "/agents/{agent_key}/container",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bind_agent_container(
    agent_key: str,
    payload: ContainerBindRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: ContainerService = Depends(_svc),
):
    try:
        await service.bind_agent(
            tenant_id=_uuid(tenant_context.tenant_id),
            agent_key=agent_key,
            container_id=payload.container_id,
        )
    except ContainerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Container not found"
        ) from None
    return None


@router.delete(
    "/agents/{agent_key}/container",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unbind_agent_container(
    agent_key: str,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: ContainerService = Depends(_svc),
):
    await service.unbind_agent(
        tenant_id=_uuid(tenant_context.tenant_id), agent_key=agent_key
    )
    return None


__all__ = ["router"]
