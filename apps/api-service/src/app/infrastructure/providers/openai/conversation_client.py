"""Lightweight OpenAI Conversations client used to bootstrap conv_* IDs."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings
from openai import AsyncOpenAI


class OpenAIConversationFactory:
    """Creates OpenAI-hosted conversations and returns their IDs."""

    def __init__(self, settings_factory: Callable[[], Settings]) -> None:
        self._settings_factory = settings_factory

    async def create(
        self,
        *,
        tenant_id: str,
        user_id: str | None,
        conversation_key: str,
    ) -> str:
        """Create a provider conversation and return its conv_* ID."""

        settings = self._settings_factory()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        metadata = {
            "tenant_id": tenant_id,
            "conversation_key": conversation_key,
        }
        if user_id:
            metadata["user_id"] = user_id

        response = await client.conversations.create(
            metadata=metadata,
        )
        return response.id


__all__ = ["OpenAIConversationFactory"]
