"""Provider-facing gateway for vector store operations (OpenAI backed)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from io import BytesIO
from typing import Any, cast

from openai import AsyncOpenAI

from app.core.settings import Settings


class OpenAIVectorStoreGateway:
    """Thin wrapper around OpenAI SDK to enable DI and future provider swaps."""

    def __init__(
        self,
        settings_factory: Callable[[], Settings],
        *,
        get_tenant_api_key: Callable[[uuid.UUID, Settings], str] | None = None,
        client_override: Callable[[uuid.UUID | str], AsyncOpenAI] | None = None,
    ) -> None:
        self._settings_factory = settings_factory
        self._get_tenant_api_key = get_tenant_api_key
        self._client_override = client_override

    def _client(self, tenant_id: uuid.UUID | str) -> AsyncOpenAI:
        if self._client_override:
            return self._client_override(tenant_id)

        tenant_uuid = uuid.UUID(str(tenant_id))
        settings = self._settings_factory()
        api_key = (
            self._get_tenant_api_key(tenant_uuid, settings)
            if self._get_tenant_api_key
            else settings.openai_api_key
        )
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return AsyncOpenAI(api_key=api_key)

    def client_for_tenant(self, tenant_id: uuid.UUID | str) -> AsyncOpenAI:
        """Expose a stable client factory for callers that need raw SDK access."""

        return self._client(tenant_id)

    # -- stores --
    async def create_store(self, *, tenant_id: uuid.UUID, payload: dict[str, Any]) -> object:
        client = self._client(tenant_id)
        return await client.vector_stores.create(**payload)

    async def delete_store(self, *, tenant_id: uuid.UUID, openai_id: str) -> None:
        client = self._client(tenant_id)
        await client.vector_stores.delete(openai_id)

    # -- files --
    async def retrieve_file_meta(self, *, tenant_id: uuid.UUID, file_id: str) -> object:
        client = self._client(tenant_id)
        return await client.files.retrieve(file_id)

    async def upload_file(
        self,
        *,
        tenant_id: uuid.UUID,
        filename: str,
        data: bytes,
        mime_type: str | None,
    ) -> object:
        client = self._client(tenant_id)
        file_tuple: tuple[object, ...]
        if mime_type:
            file_tuple = (filename, BytesIO(data), mime_type)
        else:
            file_tuple = (filename, BytesIO(data))
        return await client.files.create(file=file_tuple, purpose="assistants")

    async def delete_openai_file(self, *, tenant_id: uuid.UUID, file_id: str) -> None:
        client = self._client(tenant_id)
        await client.files.delete(file_id=file_id)

    async def attach_file(
        self,
        *,
        tenant_id: uuid.UUID,
        vector_store_openai_id: str,
        file_id: str,
        attributes: dict[str, Any] | None,
        chunking_strategy: dict[str, Any] | None,
        poll: bool,
    ) -> object:
        client = self._client(tenant_id)
        kwargs: dict[str, Any] = {
            "vector_store_id": vector_store_openai_id,
            "file_id": file_id,
        }
        if attributes is not None:
            kwargs["attributes"] = attributes
        if chunking_strategy is not None:
            kwargs["chunking_strategy"] = chunking_strategy
        if poll:
            return await client.vector_stores.files.create_and_poll(
                **cast(dict[str, Any], kwargs)
            )
        return await client.vector_stores.files.create(**cast(dict[str, Any], kwargs))

    async def delete_file(
        self, *, tenant_id: uuid.UUID, vector_store_openai_id: str, file_id: str
    ) -> None:
        client = self._client(tenant_id)
        await client.vector_stores.files.delete(
            vector_store_id=vector_store_openai_id, file_id=file_id
        )

    # -- search --
    async def search(
        self,
        *,
        tenant_id: uuid.UUID,
        vector_store_openai_id: str,
        query: str | list[str],
        filters: dict[str, Any] | None,
        max_num_results: int | None,
        ranking_options: dict[str, Any] | None,
    ) -> object:
        client = self._client(tenant_id)
        kwargs: dict[str, Any] = {"vector_store_id": vector_store_openai_id, "query": query}
        if filters:
            kwargs["filters"] = filters
        if max_num_results:
            kwargs["max_num_results"] = max_num_results
        if ranking_options:
            kwargs["ranking_options"] = ranking_options
        return await client.vector_stores.search(**cast(dict[str, Any], kwargs))


__all__ = ["OpenAIVectorStoreGateway"]
