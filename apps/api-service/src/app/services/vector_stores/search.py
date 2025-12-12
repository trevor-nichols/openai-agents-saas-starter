"""Search orchestration across vector stores."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from app.domain.vector_stores import (
    VectorStore,
    VectorStoreSearchContentChunk,
    VectorStoreSearchResult,
    VectorStoreSearchResultsPage,
)
from app.services.vector_stores.instrumentation import instrument


class VectorStoreLookup(Protocol):
    async def get_store(
        self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str
    ) -> VectorStore: ...


class VectorStoreSearchGateway(Protocol):
    async def search(
        self,
        *,
        tenant_id: uuid.UUID,
        vector_store_openai_id: str,
        query: str | list[str],
        filters: dict[str, Any] | None,
        max_num_results: int | None,
        ranking_options: dict[str, Any] | None,
    ) -> object: ...


class SearchService:
    def __init__(
        self, *, store_service: VectorStoreLookup, gateway: VectorStoreSearchGateway
    ) -> None:
        self._store_service = store_service
        self._gateway = gateway

    async def search(
        self,
        *,
        vector_store_id: uuid.UUID | str,
        tenant_id: uuid.UUID | str,
        query: str | list[str],
        filters: dict[str, Any] | None = None,
        max_num_results: int | None = None,
        ranking_options: dict[str, Any] | None = None,
    ) -> VectorStoreSearchResultsPage:
        store = await self._store_service.get_store(
            vector_store_id=vector_store_id,
            tenant_id=tenant_id,
        )
        async with instrument(
            "search", metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)}
        ):
            raw = await self._gateway.search(
                tenant_id=store.tenant_id,
                vector_store_openai_id=store.openai_id,
                query=query,
                filters=filters,
                max_num_results=max_num_results,
                ranking_options=ranking_options,
            )
        return _parse_search_response(raw)


def _parse_search_response(raw: object) -> VectorStoreSearchResultsPage:
    payload = _coerce_mapping(raw)
    data_items = payload.get("data") or []
    results: list[VectorStoreSearchResult] = []
    if isinstance(data_items, list):
        for item in data_items:
            item_payload = _coerce_mapping(item)
            chunks_raw = item_payload.get("content") or []
            chunks: list[VectorStoreSearchContentChunk] = []
            if isinstance(chunks_raw, list):
                for chunk in chunks_raw:
                    chunk_payload = _coerce_mapping(chunk)
                    if chunk_payload.get("type") == "text" and isinstance(
                        chunk_payload.get("text"), str
                    ):
                        chunks.append(
                            VectorStoreSearchContentChunk(
                                type="text",
                                text=chunk_payload["text"],
                            )
                        )
            attributes = item_payload.get("attributes") or {}
            results.append(
                VectorStoreSearchResult(
                    file_id=str(item_payload.get("file_id") or ""),
                    filename=str(item_payload.get("filename") or ""),
                    score=float(item_payload.get("score") or 0.0),
                    attributes=attributes if isinstance(attributes, dict) else {},
                    content=chunks,
                )
            )

    has_more = bool(payload.get("has_more") or False)
    next_page_raw = payload.get("next_page")
    next_page = str(next_page_raw) if isinstance(next_page_raw, str) else None
    return VectorStoreSearchResultsPage(
        object=str(payload.get("object") or "vector_store.search_results.page"),
        search_query=str(payload.get("search_query") or ""),
        data=results,
        has_more=has_more,
        next_page=next_page,
    )


def _coerce_mapping(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    model_dump = getattr(raw, "model_dump", None)
    if callable(model_dump):
        value = model_dump()
        if isinstance(value, dict):
            return value
    to_dict = getattr(raw, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        if isinstance(value, dict):
            return value
    return {}


__all__ = ["SearchService"]
