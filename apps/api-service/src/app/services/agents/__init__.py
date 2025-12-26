"""Agent orchestration services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.agents.context import ConversationActorContext

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from app.services.agents.factory import build_agent_service, get_agent_service
    from app.services.agents.service import AgentService

__all__ = ["AgentService", "ConversationActorContext", "build_agent_service", "get_agent_service"]


def __getattr__(name: str):
    if name == "AgentService":
        from app.services.agents.service import AgentService as _AgentService

        return _AgentService
    if name in {"build_agent_service", "get_agent_service"}:
        from app.services.agents.factory import build_agent_service as _build_agent_service
        from app.services.agents.factory import get_agent_service as _get_agent_service

        return _build_agent_service if name == "build_agent_service" else _get_agent_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
