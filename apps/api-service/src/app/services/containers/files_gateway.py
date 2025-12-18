"""Provider-facing gateway for container file operations (OpenAI backed)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, cast, runtime_checkable

from openai import AsyncOpenAI

from app.core.settings import Settings


@dataclass(slots=True)
class ContainerFileContent:
    data: bytes
    filename: str | None = None


@runtime_checkable
class ContainerFilesGateway(Protocol):
    async def download_file_content(
        self,
        *,
        tenant_id: uuid.UUID | str,
        container_id: str,
        file_id: str,
    ) -> ContainerFileContent: ...


class OpenAIContainerFilesGateway:
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

    async def download_file_content(
        self,
        *,
        tenant_id: uuid.UUID | str,
        container_id: str,
        file_id: str,
    ) -> ContainerFileContent:
        client = self._client(tenant_id)
        resp = await cast(Any, client).containers.files.content(
            container_id=container_id,
            file_id=file_id,
        )
        filename = getattr(resp, "filename", None)
        data = await resp.aread()
        return ContainerFileContent(data=data, filename=filename)


__all__ = [
    "ContainerFileContent",
    "ContainerFilesGateway",
    "OpenAIContainerFilesGateway",
]
