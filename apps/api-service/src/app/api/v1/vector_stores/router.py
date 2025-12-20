"""Tenant-scoped vector store CRUD, file attach, and search endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.v1.vector_stores.deps import tenant_admin, tenant_viewer
from app.api.v1.vector_stores.schemas import (
    VectorStoreCreateRequest,
    VectorStoreFileCreateRequest,
    VectorStoreFileListResponse,
    VectorStoreFileResponse,
    VectorStoreFileUploadRequest,
    VectorStoreListResponse,
    VectorStoreResponse,
    VectorStoreSearchRequest,
    VectorStoreSearchResponse,
)
from app.bootstrap.container import get_container, wire_vector_store_service
from app.services.agents.vector_store_access import (
    AgentVectorStoreAccessError,
    AgentVectorStoreAccessService,
)
from app.services.vector_stores import (
    VectorStoreFileConflictError,
    VectorStoreNameConflictError,
    VectorStoreNotFoundError,
    VectorStoreQuotaError,
    VectorStoreService,
    VectorStoreValidationError,
)

router = APIRouter(prefix="/vector-stores", tags=["vector-stores"])


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # pragma: no cover - FastAPI validation should catch
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID"
        ) from exc


def _svc() -> VectorStoreService:
    container = get_container()
    if container.vector_store_service is None:
        wire_vector_store_service(container)
    if container.vector_store_service is None:
        raise RuntimeError("VectorStoreService is not configured")
    return container.vector_store_service


def _store_response(store) -> VectorStoreResponse:
    return VectorStoreResponse(
        id=store.id,
        openai_id=store.openai_id,
        tenant_id=store.tenant_id,
        owner_user_id=store.owner_user_id,
        name=store.name,
        description=store.description,
        status=store.status,
        usage_bytes=store.usage_bytes,
        expires_after=store.expires_after,
        expires_at=store.expires_at,
        last_active_at=store.last_active_at,
        metadata=store.metadata_json or {},
        created_at=store.created_at,
        updated_at=store.updated_at,
    )


def _file_response(file, store_id: uuid.UUID) -> VectorStoreFileResponse:
    return VectorStoreFileResponse(
        id=file.id,
        openai_file_id=file.openai_file_id,
        vector_store_id=store_id,
        filename=file.filename,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        usage_bytes=file.usage_bytes,
        status=file.status,
        attributes=file.attributes_json or {},
        chunking_strategy=file.chunking_json,
        last_error=file.last_error,
        created_at=file.created_at,
        updated_at=file.updated_at,
    )


@router.post("", response_model=VectorStoreResponse, status_code=status.HTTP_201_CREATED)
async def create_vector_store(
    payload: VectorStoreCreateRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreResponse:
    owner_user = current_user.get("user_id") if isinstance(current_user, dict) else None
    owner_uuid = _uuid(owner_user) if owner_user else None
    try:
        store = await service.create_store(
            tenant_id=_uuid(tenant_context.tenant_id),
            owner_user_id=owner_uuid,
            name=payload.name,
            description=payload.description,
            expires_after=payload.expires_after,
            metadata=payload.metadata,
        )
    except VectorStoreQuotaError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VectorStoreNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _store_response(store)


@router.get("", response_model=VectorStoreListResponse)
async def list_vector_stores(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreListResponse:
    stores, total = await service.list_stores(
        tenant_id=_uuid(tenant_context.tenant_id), limit=limit, offset=offset
    )
    return VectorStoreListResponse(items=[_store_response(s) for s in stores], total=total)


@router.get("/{vector_store_id}", response_model=VectorStoreResponse)
async def get_vector_store(
    vector_store_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreResponse:
    try:
        store = await service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    return _store_response(store)


@router.delete("/{vector_store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vector_store(
    vector_store_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
):
    try:
        await service.delete_store(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    return None


@router.post(
    "/{vector_store_id}/files",
    response_model=VectorStoreFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_file(
    vector_store_id: uuid.UUID,
    payload: VectorStoreFileCreateRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreFileResponse:
    try:
        file = await service.attach_file(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            file_id=payload.file_id,
            attributes=payload.attributes,
            chunking_strategy=payload.chunking_strategy,
            poll=payload.poll,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    except VectorStoreFileConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except VectorStoreValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VectorStoreQuotaError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - translated to 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _file_response(file, vector_store_id)


@router.post(
    "/{vector_store_id}/files/upload",
    response_model=VectorStoreFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_and_attach_file(
    vector_store_id: uuid.UUID,
    payload: VectorStoreFileUploadRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreFileResponse:
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
    agent_key = payload.agent_key
    try:
        if agent_key:
            access = AgentVectorStoreAccessService(vector_store_service=service)
            await access.assert_agent_can_attach(
                agent_key=agent_key,
                tenant_id=str(tenant_context.tenant_id),
                user_id=str(user_id) if user_id else None,
                vector_store_id=str(vector_store_id),
            )
        file = await service.attach_storage_object(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            object_id=payload.object_id,
            attributes=payload.attributes,
            chunking_strategy=payload.chunking_strategy,
            poll=payload.poll,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AgentVectorStoreAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except VectorStoreFileConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except VectorStoreValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VectorStoreQuotaError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - translated to 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _file_response(file, vector_store_id)


@router.get("/{vector_store_id}/files", response_model=VectorStoreFileListResponse)
async def list_files(
    vector_store_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreFileListResponse:
    try:
        files, total = await service.list_files(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None

    return VectorStoreFileListResponse(
        items=[_file_response(f, vector_store_id) for f in files], total=total
    )


@router.get("/{vector_store_id}/files/{file_id}", response_model=VectorStoreFileResponse)
async def get_file(
    vector_store_id: uuid.UUID,
    file_id: str,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreFileResponse:
    try:
        file = await service.get_file(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            openai_file_id=file_id,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        ) from None

    return _file_response(file, vector_store_id)


@router.delete("/{vector_store_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    vector_store_id: uuid.UUID,
    file_id: str,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
):
    try:
        await service.delete_file(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            file_id=file_id,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        ) from None
    return None


@router.post("/{vector_store_id}/search", response_model=VectorStoreSearchResponse)
async def search_vector_store(
    vector_store_id: uuid.UUID,
    payload: VectorStoreSearchRequest,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_viewer),
    service: VectorStoreService = Depends(_svc),
) -> VectorStoreSearchResponse:
    try:
        result = await service.search(
            vector_store_id=vector_store_id,
            tenant_id=_uuid(tenant_context.tenant_id),
            query=payload.query,
            filters=payload.filters,
            max_num_results=payload.max_num_results,
            ranking_options=payload.ranking_options,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    return VectorStoreSearchResponse.from_domain(result)


@router.post(
    "/{vector_store_id}/bindings/{agent_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bind_agent_to_vector_store(
    vector_store_id: uuid.UUID,
    agent_key: str,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
):
    try:
        await service.bind_agent_to_store(
            tenant_id=_uuid(tenant_context.tenant_id),
            agent_key=agent_key,
            vector_store_id=vector_store_id,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vector store not found"
        ) from None
    return None


@router.delete(
    "/{vector_store_id}/bindings/{agent_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unbind_agent_from_vector_store(
    vector_store_id: uuid.UUID,
    agent_key: str,
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_context=Depends(tenant_admin),
    service: VectorStoreService = Depends(_svc),
):
    await service.unbind_agent_from_store(
        tenant_id=_uuid(tenant_context.tenant_id),
        agent_key=agent_key,
        vector_store_id=vector_store_id,
    )
    return None
