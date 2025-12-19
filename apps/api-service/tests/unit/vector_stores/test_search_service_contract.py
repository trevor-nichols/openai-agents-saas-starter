from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.domain.vector_stores import VectorStore
from app.services.vector_stores.search import SearchService


class _StoreServiceStub:
    async def get_store(self, *, vector_store_id: uuid.UUID | str, tenant_id: uuid.UUID | str):
        return VectorStore(
            id=uuid.UUID(str(vector_store_id)),
            openai_id="vs_openai",
            tenant_id=uuid.UUID(str(tenant_id)),
            owner_user_id=None,
            name="primary",
            description=None,
            status="ready",
            usage_bytes=0,
            expires_after=None,
            expires_at=None,
            last_active_at=None,
            metadata={},
        )


class _GatewayStub:
    async def search(self, *, tenant_id, vector_store_openai_id, query, filters, max_num_results, ranking_options):
        return {
            "object": "vector_store.search_results.page",
            "search_query": query if isinstance(query, str) else " / ".join(query),
            "data": [
                {
                    "file_id": "file_123",
                    "filename": "doc.pdf",
                    "score": 0.95,
                    "attributes": {"author": "John"},
                    "content": [{"type": "text", "text": "Relevant chunk"}],
                }
            ],
            "has_more": False,
            "next_page": None,
        }


@pytest.mark.asyncio
async def test_vector_store_search_returns_typed_page() -> None:
    svc = SearchService(store_service=_StoreServiceStub(), gateway=_GatewayStub())
    tenant_id = uuid.uuid4()
    store_id = uuid.uuid4()

    page = await svc.search(
        vector_store_id=store_id,
        tenant_id=tenant_id,
        query="What is the return policy?",
        filters=None,
        max_num_results=10,
        ranking_options=None,
    )

    assert page.object == "vector_store.search_results.page"
    assert page.search_query
    assert page.has_more is False
    assert page.next_page is None
    assert len(page.data) == 1
    result = page.data[0]
    assert result.file_id == "file_123"
    assert result.filename == "doc.pdf"
    assert result.score == pytest.approx(0.95)
    assert result.attributes["author"] == "John"
    assert result.content[0].type == "text"
    assert result.content[0].text == "Relevant chunk"

