"""Agent binding orchestration for vector stores."""

from __future__ import annotations

import uuid

from app.domain.vector_stores import AgentVectorStoreBinding, AgentVectorStoreRepository
from app.services.vector_stores.stores import StoreService
from app.services.vector_stores.utils import coerce_uuid


class BindingService:
    def __init__(
        self,
        *,
        store_service: StoreService,
        binding_repo: AgentVectorStoreRepository,
    ) -> None:
        self._store_service = store_service
        self._binding_repo = binding_repo

    async def get_agent_binding(
        self, *, tenant_id: uuid.UUID | str, agent_key: str
    ) -> AgentVectorStoreBinding | None:
        tenant_uuid = coerce_uuid(tenant_id)
        return await self._binding_repo.get_binding(tenant_id=tenant_uuid, agent_key=agent_key)

    async def bind_agent_to_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> AgentVectorStoreBinding:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        binding = AgentVectorStoreBinding(
            agent_key=agent_key,
            vector_store_id=store.id,
            tenant_id=store.tenant_id,
        )
        return await self._binding_repo.upsert_binding(binding)

    async def unbind_agent_from_store(
        self,
        *,
        tenant_id: uuid.UUID | str,
        agent_key: str,
        vector_store_id: uuid.UUID | str,
    ) -> None:
        tenant_uuid = coerce_uuid(tenant_id)
        store_uuid = coerce_uuid(vector_store_id)
        await self._binding_repo.delete_binding(
            tenant_id=tenant_uuid, agent_key=agent_key, vector_store_id=store_uuid
        )


__all__ = ["BindingService"]
