"""Concrete OpenAI agent provider wiring registry, runtime, and sessions."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.settings import Settings
from app.domain.ai import AgentDescriptor
from app.domain.ai.ports import AgentProvider

from .conversation_client import OpenAIConversationFactory
from .registry import OpenAIAgentRegistry
from .runtime import OpenAIAgentRuntime
from .session_store import OpenAISQLAlchemySessionStore

if TYPE_CHECKING:
    from app.guardrails._shared.registry import GuardrailRegistry

logger = logging.getLogger(__name__)


class OpenAIAgentProvider(AgentProvider):
    """Provider implementation backed by the OpenAI Agents SDK."""

    name = "openai"

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings],
        conversation_searcher: Callable[[str, str], Awaitable[object]],
        session_store: OpenAISQLAlchemySessionStore,
        conversation_factory: OpenAIConversationFactory,
        guardrail_registry: GuardrailRegistry | None = None,
    ) -> None:
        self._registry = OpenAIAgentRegistry(
            settings_factory=settings_factory,
            conversation_searcher=conversation_searcher,
            guardrail_registry=guardrail_registry,
        )
        self._runtime = OpenAIAgentRuntime(self._registry)
        self._session_store = session_store
        self._conversation_factory = conversation_factory

    @property
    def runtime(self) -> OpenAIAgentRuntime:
        return self._runtime

    @property
    def session_store(self) -> OpenAISQLAlchemySessionStore:
        return self._session_store

    @property
    def conversation_factory(self) -> OpenAIConversationFactory:
        return self._conversation_factory

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

    def mark_seen(self, agent_key: str, ts: datetime) -> None:
        self._registry.mark_seen(agent_key, ts)


def build_openai_provider(
    *,
    settings_factory: Callable[[], Settings],
    conversation_searcher: Callable[[str, str], Awaitable[object]],
    engine: AsyncEngine,
    auto_create_tables: bool | None = None,
    enable_guardrails: bool = True,
) -> OpenAIAgentProvider:
    """Build an OpenAI agent provider with all dependencies.

    Args:
        settings_factory: Factory function to retrieve Settings.
        conversation_searcher: Async callable for searching conversations.
        engine: SQLAlchemy async engine for persistence.
        auto_create_tables: Whether to auto-create tables (None = use settings default).
        enable_guardrails: Whether to initialize the guardrail system. Default True.

    Returns:
        Configured OpenAIAgentProvider instance.
    """
    conversation_factory = OpenAIConversationFactory(settings_factory)
    session_store = OpenAISQLAlchemySessionStore(
        engine,
        auto_create_tables=auto_create_tables,
    )

    # Initialize guardrail registry if enabled
    guardrail_registry: GuardrailRegistry | None = None
    if enable_guardrails:
        try:
            from app.guardrails._shared.loaders import initialize_guardrails
            from app.guardrails._shared.registry import get_guardrail_registry

            initialize_guardrails()
            guardrail_registry = get_guardrail_registry()
            logger.info(
                "Guardrail system initialized: %d specs, %d presets",
                len(guardrail_registry.list_specs()),
                len(guardrail_registry.list_presets()),
            )
        except ImportError:
            logger.warning("Guardrails module not available, skipping initialization")
        except Exception as e:
            logger.exception("Failed to initialize guardrails: %s", e)

    return OpenAIAgentProvider(
        settings_factory=settings_factory,
        conversation_searcher=conversation_searcher,
        session_store=session_store,
        conversation_factory=conversation_factory,
        guardrail_registry=guardrail_registry,
    )


__all__ = ["OpenAIAgentProvider", "build_openai_provider"]
