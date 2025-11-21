"""Concrete OpenAI agent provider wiring registry, runtime, and sessions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.settings import Settings
from app.domain.ai import AgentDescriptor
from app.domain.ai.ports import AgentProvider

from .registry import OpenAIAgentRegistry
from .runtime import OpenAIAgentRuntime
from .session_store import OpenAISQLAlchemySessionStore


class OpenAIAgentProvider(AgentProvider):
    """Provider implementation backed by the OpenAI Agents SDK."""

    name = "openai"

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings],
        conversation_searcher: Callable[[str, str], Awaitable[object]],
        session_store: OpenAISQLAlchemySessionStore,
    ) -> None:
        self._registry = OpenAIAgentRegistry(
            settings_factory=settings_factory,
            conversation_searcher=conversation_searcher,
        )
        self._runtime = OpenAIAgentRuntime(self._registry)
        self._session_store = session_store

    @property
    def runtime(self) -> OpenAIAgentRuntime:
        return self._runtime

    @property
    def session_store(self) -> OpenAISQLAlchemySessionStore:
        return self._session_store

    def list_agents(self):
        return self._registry.list_descriptors()

    def resolve_agent(self, preferred_key: str | None = None) -> AgentDescriptor:
        return self._registry.resolve_agent(preferred_key)

    def get_agent(self, agent_key: str) -> AgentDescriptor | None:
        return self._registry.get_descriptor(agent_key)

    def default_agent_key(self) -> str:
        return self._registry.default_agent_key

    def tool_overview(self):
        return self._registry.tool_overview()


def build_openai_provider(
    *,
    settings_factory: Callable[[], Settings],
    conversation_searcher: Callable[[str, str], Awaitable[object]],
    engine: AsyncEngine,
    auto_create_tables: bool | None = None,
) -> OpenAIAgentProvider:
    session_store = OpenAISQLAlchemySessionStore(
        engine,
        auto_create_tables=auto_create_tables,
    )
    return OpenAIAgentProvider(
        settings_factory=settings_factory,
        conversation_searcher=conversation_searcher,
        session_store=session_store,
    )


__all__ = ["OpenAIAgentProvider", "build_openai_provider"]
