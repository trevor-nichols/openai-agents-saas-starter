"""Domain ports describing the provider integration surface."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from .models import AgentDescriptor, AgentRunResult, AgentRunUsage, AgentStreamEvent


AgentSessionHandle = Any


@runtime_checkable
class AgentSessionStore(Protocol):
    """Abstract factory for creating provider session handles."""

    def build(self, session_id: str) -> AgentSessionHandle:
        """Return a provider-specific session handle for the given conversation."""


@runtime_checkable
class AgentStreamingHandle(Protocol):
    """Represents an active streaming run for an agent."""

    def events(self) -> AsyncIterator[AgentStreamEvent]:
        ...

    @property
    def last_response_id(self) -> str | None:
        ...

    @property
    def usage(self) -> AgentRunUsage | None:
        ...


@runtime_checkable
class AgentRuntime(Protocol):
    """Executes agent interactions for a specific provider."""

    async def run(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgentRunResult:
        ...

    def run_stream(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgentStreamingHandle:
        ...


@runtime_checkable
class AgentProvider(Protocol):
    """High-level provider abstraction exposed to application services."""

    name: str

    @property
    def runtime(self) -> AgentRuntime:
        ...

    @property
    def session_store(self) -> AgentSessionStore:
        ...

    def list_agents(self) -> Sequence[AgentDescriptor]:
        ...

    def resolve_agent(self, preferred_key: str | None = None) -> AgentDescriptor:
        ...

    def get_agent(self, agent_key: str) -> AgentDescriptor | None:
        ...

    def default_agent_key(self) -> str:
        ...

    def tool_overview(self) -> Mapping[str, Any]:
        ...


__all__ = [
    "AgentProvider",
    "AgentRuntime",
    "AgentSessionHandle",
    "AgentSessionStore",
    "AgentStreamingHandle",
]
