"""Proxy download endpoints for OpenAI file & container file outputs."""

from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from openai import AsyncOpenAI

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.core.settings import get_settings
from app.services.containers import ContainerNotFoundError, container_service
from app.services.vector_stores import VectorStoreNotFoundError, vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openai", tags=["openai-files"])


def _client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


@router.get("/files/{file_id}/download")
async def download_openai_file(
    file_id: str,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    client: AsyncOpenAI = Depends(_client),
):
    try:
        await vector_store_service.get_file_by_openai_id(
            tenant_id=tenant_context.tenant_id,
            openai_file_id=file_id,
        )
    except VectorStoreNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        ) from None

    try:
        resp = await cast(Any, client).files.content(file_id)
    except Exception as exc:  # pragma: no cover - network/runtime errors
        logger.warning("openai.file_download.failed", exc_info=exc, extra={"file_id": file_id})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch file from OpenAI",
        ) from exc

    filename = getattr(resp, "filename", None) or f"{file_id}.bin"
    content_bytes = await resp.aread()
    return Response(
        content=content_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/containers/{container_id}/files/{file_id}/download")
async def download_openai_container_file(
    container_id: str,
    file_id: str,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    client: AsyncOpenAI = Depends(_client),
):
    try:
        await container_service.get_container_by_openai_id(
            openai_container_id=container_id,
            tenant_id=tenant_context.tenant_id,
        )
    except ContainerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        ) from None

    try:
        resp = await cast(Any, client).containers.files.content(
            container_id=container_id,
            file_id=file_id,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "openai.container_file_download.failed",
            exc_info=exc,
            extra={"file_id": file_id, "container_id": container_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch container file from OpenAI",
        ) from exc

    filename = getattr(resp, "filename", None) or f"{file_id}.bin"
    content_bytes = await resp.aread()
    return Response(
        content=content_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )
