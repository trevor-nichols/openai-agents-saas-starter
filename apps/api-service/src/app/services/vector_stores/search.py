"""Search orchestration across vector stores."""

from __future__ import annotations

import uuid
from typing import Any

from app.services.vector_stores.gateway import OpenAIVectorStoreGateway
from app.services.vector_stores.instrumentation import instrument
from app.services.vector_stores.stores import StoreService


class SearchService:
    def __init__(self, *, store_service: StoreService, gateway: OpenAIVectorStoreGateway) -> None:
        self._store_service = store_service
        self._gateway = gateway

    async def search(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        query: str,
        filters: dict[str, Any] | None = None,
        max_num_results: int | None = None,
        ranking_options: dict[str, Any] | None = None,
    ) -> Any:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        async with instrument(
            "search", metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)}
        ):
            return await self._gateway.search(
                tenant_id=store.tenant_id,
                vector_store_openai_id=store.openai_id,
                query=query,
                filters=filters,
                max_num_results=max_num_results,
                ranking_options=ranking_options,
            )


__all__ = ["SearchService"]
