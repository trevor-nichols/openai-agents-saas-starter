"""Facade for vector store operations built from modular sub-services."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domain.vector_stores import (
    AgentVectorStoreBinding,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileConflictError,
    VectorStoreNameConflictError,
    VectorStoreNotFoundError,
    VectorStoreQuotaError,
    VectorStoreValidationError,
)
from app.infrastructure.persistence.vector_stores.repository import (
    SqlAlchemyAgentVectorStoreRepository,
    SqlAlchemyVectorStoreFileRepository,
    SqlAlchemyVectorStoreRepository,
)
from app.services.vector_stores.bindings import BindingService
from app.services.vector_stores.files import FileService
from app.services.vector_stores.gateway import OpenAIVectorStoreGateway
from app.services.vector_stores.limits import VectorLimitResolver
from app.services.vector_stores.policy import VectorStorePolicy
from app.services.vector_stores.search import SearchService
from app.services.vector_stores.stores import StoreService


class VectorStoreService:
    """High-level façade that delegates to modular store/file/binding/search services."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings_factory: Callable[[], Settings],
        *,
        get_tenant_api_key: Callable[[uuid.UUID, Settings], str] | None = None,
        limit_resolver: VectorLimitResolver | None = None,
        client_factory: Callable[[uuid.UUID | str], AsyncOpenAI] | None = None,
    ) -> None:
        store_repo = SqlAlchemyVectorStoreRepository(session_factory)
        file_repo = SqlAlchemyVectorStoreFileRepository(session_factory)
        binding_repo = SqlAlchemyAgentVectorStoreRepository(session_factory)
        gateway = OpenAIVectorStoreGateway(
            settings_factory,
            get_tenant_api_key=get_tenant_api_key,
            client_override=client_factory,
        )
        limit_resolver = limit_resolver or VectorLimitResolver(
            billing_service=None, settings_factory=settings_factory
        )
        policy = VectorStorePolicy(limit_resolver, settings_factory)

        self._gateway = gateway
        self._stores = StoreService(store_repo=store_repo, policy=policy, gateway=gateway)
        self._files = FileService(
            store_service=self._stores,
            store_repo=store_repo,
            file_repo=file_repo,
            policy=policy,
            gateway=gateway,
        )
        self._bindings = BindingService(store_service=self._stores, binding_repo=binding_repo)
        self._search = SearchService(store_service=self._stores, gateway=gateway)

    # --- store facade ---
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
        return await self._stores.create_store(
            tenant_id=tenant_id,
            owner_user_id=owner_user_id,
            name=name,
            description=description,
            expires_after=expires_after,
            metadata=metadata,
        )

    async def list_stores(
        self, *, tenant_id: uuid.UUID | str, limit: int = 50, offset: int = 0
    ) -> tuple[list[VectorStore], int]:
        return await self._stores.list_stores(tenant_id=tenant_id, limit=limit, offset=offset)

    async def ensure_primary_store(
        self, *, tenant_id: uuid.UUID | str, owner_user_id: uuid.UUID | str | None = None
    ) -> VectorStore:
        return await self._stores.ensure_primary_store(
            tenant_id=tenant_id,
            owner_user_id=owner_user_id,
        )

    async def get_store_by_name(
        self, *, tenant_id: uuid.UUID | str, name: str
    ) -> VectorStore | None:
        return await self._stores.get_store_by_name(tenant_id=tenant_id, name=name)

    async def get_store_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_id: str
    ) -> VectorStore | None:
        return await self._stores.get_store_by_openai_id(tenant_id=tenant_id, openai_id=openai_id)

    async def get_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> VectorStore:
        return await self._stores.get_store(vector_store_id=vector_store_id, tenant_id=tenant_id)

    async def delete_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> None:
        return await self._stores.delete_store(vector_store_id=vector_store_id, tenant_id=tenant_id)

    # --- file facade ---
    async def attach_file(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        file_id: str,
        attributes: dict[str, Any] | None = None,
        chunking_strategy: dict[str, Any] | None = None,
        poll: bool = True,
    ) -> VectorStoreFile:
        return await self._files.attach_file(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
            file_id=file_id,
            attributes=attributes,
            chunking_strategy=chunking_strategy,
            poll=poll,
        )

    async def list_files(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[VectorStoreFile], int]:
        return await self._files.list_files(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_file(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        openai_file_id: str,
    ) -> VectorStoreFile:
        return await self._files.get_file(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
            openai_file_id=openai_file_id,
        )

    async def delete_file(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str, file_id: str
    ) -> None:
        return await self._files.delete_file(
            vector_store_id=vector_store_id, tenant_id=tenant_id, file_id=file_id
        )

    async def get_file_by_openai_id(
        self, *, tenant_id: uuid.UUID | str, openai_file_id: str
    ) -> VectorStoreFile:
        return await self._files.get_file_by_openai_id(
            tenant_id=tenant_id, openai_file_id=openai_file_id
        )

    # --- search facade ---
    async def search(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        query: str | list[str],
        filters: dict[str, Any] | None = None,
        max_num_results: int | None = None,
        ranking_options: dict[str, Any] | None = None,
    ):
        return await self._search.search(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
            query=query,
            filters=filters,
            max_num_results=max_num_results,
            ranking_options=ranking_options,
        )

    # --- binding facade ---
    async def get_agent_binding(
        self, *, tenant_id: uuid.UUID | str, agent_key: str
    ) -> AgentVectorStoreBinding | None:
        return await self._bindings.get_agent_binding(tenant_id=tenant_id, agent_key=agent_key)

    async def bind_agent_to_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> AgentVectorStoreBinding:
        return await self._bindings.bind_agent_to_store(
            tenant_id=tenant_id, agent_key=agent_key, vector_store_id=vector_store_id
        )

    async def unbind_agent_from_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> None:
        return await self._bindings.unbind_agent_from_store(
            tenant_id=tenant_id, agent_key=agent_key, vector_store_id=vector_store_id
        )

    # --- internal helpers ---
    def openai_client(self, tenant_id: uuid.UUID | str) -> AsyncOpenAI:
        """Exposed for the sync worker to reuse the configured client factory."""

        return self._gateway.client_for_tenant(uuid.UUID(str(tenant_id)))


__all__ = [
    "VectorStoreService",
    "VectorStoreFileConflictError",
    "VectorStoreNameConflictError",
    "VectorStoreNotFoundError",
    "VectorStoreQuotaError",
    "VectorStoreValidationError",
]
