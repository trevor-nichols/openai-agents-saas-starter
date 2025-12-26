"""Store-level orchestration (create/list/get/delete)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.exc import IntegrityError

from app.domain.vector_stores import (
    VectorStore,
    VectorStoreNameConflictError,
    VectorStoreNotFoundError,
    VectorStoreRepository,
)
from app.services.vector_stores.gateway import OpenAIVectorStoreGateway
from app.services.vector_stores.instrumentation import instrument
from app.services.vector_stores.policy import VectorStorePolicy
from app.services.vector_stores.utils import (
    coerce_datetime,
    coerce_uuid,
    coerce_uuid_optional,
)

logger = logging.getLogger(__name__)


class StoreService:
    def __init__(
        self,
        *,
        store_repo: VectorStoreRepository,
        policy: VectorStorePolicy,
        gateway: OpenAIVectorStoreGateway,
    ) -> None:
        self._store_repo = store_repo
        self._policy = policy
        self._gateway = gateway

    async def create_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        owner_user_id: uuid.UUID | str | None,
        name: str,
        description: str | None = None,
        expires_after: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VectorStore:
        tenant_uuid = coerce_uuid(tenant_id)
        owner_uuid = coerce_uuid_optional(owner_user_id)

        await self._policy.ensure_store_can_be_created(
            tenant_id=tenant_uuid, name=name, store_repo=self._store_repo
        )

        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if expires_after is not None:
            payload["expires_after"] = expires_after
        if metadata is not None:
            payload["metadata"] = metadata

        try:
            async with instrument(
                "create", metadata={"tenant_id": str(tenant_uuid), "name": name}
            ):
                remote = cast(
                    Any, await self._gateway.create_store(tenant_id=tenant_uuid, payload=payload)
                )
        except Exception:
            logger.warning(
                "vector_store.create.failed", extra={"tenant_id": str(tenant_uuid)}, exc_info=True
            )
            raise

        usage_bytes = getattr(remote, "usage_bytes", None) or getattr(remote, "bytes", 0) or 0
        status = getattr(remote, "status", None) or "ready"
        expires_at = coerce_datetime(getattr(remote, "expires_at", None))
        last_active_at = coerce_datetime(getattr(remote, "last_active_at", None))

        store = VectorStore(
            id=uuid.uuid4(),
            openai_id=remote.id,
            tenant_id=tenant_uuid,
            owner_user_id=owner_uuid,
            name=name,
            description=description,
            status=status,
            usage_bytes=usage_bytes,
            expires_after=expires_after,
            expires_at=expires_at,
            last_active_at=last_active_at,
            metadata=metadata or {},
            created_at=datetime.now(UTC),
        )

        try:
            return await self._store_repo.create(store)
        except IntegrityError as exc:
            # best-effort cleanup of remote resource
            await self._safe_delete_remote_store(tenant_uuid, store.openai_id)
            raise VectorStoreNameConflictError(
                "A vector store with this name already exists"
            ) from exc
        except Exception:
            await self._safe_delete_remote_store(tenant_uuid, store.openai_id)
            raise

    async def list_stores(
        self, *, tenant_id: uuid.UUID | str, limit: int = 50, offset: int = 0
    ) -> tuple[list[VectorStore], int]:
        tenant_uuid = coerce_uuid(tenant_id)
        return await self._store_repo.list(tenant_id=tenant_uuid, limit=limit, offset=offset)

    async def ensure_primary_store(
        self, *, tenant_id: uuid.UUID | str, owner_user_id: uuid.UUID | str | None = None
    ) -> VectorStore:
        tenant_uuid = coerce_uuid(tenant_id)
        owner_uuid = coerce_uuid_optional(owner_user_id)

        existing = await self._store_repo.get_by_name(tenant_id=tenant_uuid, name="primary")
        if existing:
            return existing

        return await self.create_store(
            tenant_id=tenant_uuid,
            owner_user_id=owner_uuid,
            name="primary",
            description="Default tenant vector store",
        )

    async def get_store_by_name(
        self, *, tenant_id: uuid.UUID | str, name: str
    ) -> VectorStore | None:
        tenant_uuid = coerce_uuid(tenant_id)
        return await self._store_repo.get_by_name(tenant_id=tenant_uuid, name=name)

    async def get_store_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_id: str
    ) -> VectorStore | None:
        tenant_uuid = coerce_uuid(tenant_id)
        return await self._store_repo.get_by_openai_id(tenant_id=tenant_uuid, openai_id=openai_id)

    async def get_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> VectorStore:
        store = await self._get_store(vector_store_id, tenant_id)
        return store

    async def delete_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> None:
        store = await self._get_store(vector_store_id, tenant_id)
        try:
            async with instrument(
                "delete_store",
                metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            ):
                await self._gateway.delete_store(
                    tenant_id=store.tenant_id, openai_id=store.openai_id
                )
        except Exception:
            logger.warning(
                "vector_store.delete.failed",
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
                exc_info=True,
            )
            raise

        await self._store_repo.soft_delete(store.id)

    async def _get_store(
        self, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> VectorStore:
        vector_store_uuid = coerce_uuid(vector_store_id)
        tenant_uuid = coerce_uuid(tenant_id)
        store = await self._store_repo.get(vector_store_uuid)
        if store is None or store.deleted_at is not None:
            raise VectorStoreNotFoundError(f"Vector store {vector_store_id} not found")
        if store.tenant_id != tenant_uuid:
            raise VectorStoreNotFoundError(f"Vector store {vector_store_id} not found")
        return store

    async def _safe_delete_remote_store(self, tenant_id: uuid.UUID, openai_id: str) -> None:
        try:
            await self._gateway.delete_store(tenant_id=tenant_id, openai_id=openai_id)
        except Exception:  # pragma: no cover - defensive cleanup
            logger.warning(
                "vector_store.cleanup_failed",
                exc_info=True,
                extra={"tenant_id": str(tenant_id), "remote_id": openai_id},
            )


__all__ = ["StoreService"]
