"""Proxy download endpoints for OpenAI file & container file outputs."""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from openai import AsyncOpenAI

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.bootstrap.container import (
    get_container,
    wire_container_service,
    wire_vector_store_service,
)
from app.core.settings import get_settings
from app.domain.conversations import ConversationNotFoundError
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.conversations.ledger_query_store import (
    ConversationLedgerQueryStore,
)
from app.services.containers import ContainerNotFoundError, ContainerService
from app.services.vector_stores import VectorStoreNotFoundError
from app.utils.filenames import sanitize_download_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openai", tags=["openai-files"])


def _client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _vector_store_service():
    container = get_container()
    if container.vector_store_service is None:
        wire_vector_store_service(container)
    if container.vector_store_service is None:
        raise RuntimeError("Vector store service is not configured")
    return container.vector_store_service


def _container_service() -> ContainerService:
    container = get_container()
    if container.container_service is None:
        wire_container_service(container)
    if container.container_service is None:
        raise RuntimeError("ContainerService is not configured")
    return container.container_service


def _ledger_query_store() -> ConversationLedgerQueryStore:
    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()
    if container.session_factory is None:  # pragma: no cover - defensive
        raise RuntimeError("Session factory must be configured before ledger query store")
    return ConversationLedgerQueryStore(container.session_factory)


@router.get("/files/{file_id}/download")
async def download_openai_file(
    file_id: str,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    client: AsyncOpenAI = Depends(_client),
    vector_store_service=Depends(_vector_store_service),
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
    conversation_id: str | None = None,
    filename: str | None = None,
    _: CurrentUser = Depends(require_verified_user()),
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    client: AsyncOpenAI = Depends(_client),
    containers: ContainerService = Depends(_container_service),
    ledger: ConversationLedgerQueryStore = Depends(_ledger_query_store),
):
    # Access control for downloads:
    # - Explicit containers: require a matching local Container row
    # - Auto containers: require a ledger citation in the referenced conversation
    tenant_uuid = uuid.UUID(str(tenant_context.tenant_id))
    authorized = False
    try:
        await containers.get_container_by_openai_id(
            openai_container_id=container_id,
            tenant_id=tenant_uuid,
        )
        authorized = True
    except ContainerNotFoundError:
        authorized = False

    if not authorized:
        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found",
            ) from None
        try:
            authorized = await ledger.has_container_file_citation(
                conversation_id,
                tenant_id=tenant_context.tenant_id,
                container_id=container_id,
                file_id=file_id,
            )
        except ConversationNotFoundError:
            authorized = False
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "openai.container_file_download.ledger_check_failed",
                exc_info=exc,
                extra={
                    "container_id": container_id,
                    "file_id": file_id,
                    "conversation_id": conversation_id,
                },
            )
            authorized = False

        if not authorized:
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

    preferred_filename = sanitize_download_filename(filename)
    filename = preferred_filename or getattr(resp, "filename", None) or f"{file_id}.bin"
    content_bytes = await resp.aread()
    return Response(
        content=content_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )
