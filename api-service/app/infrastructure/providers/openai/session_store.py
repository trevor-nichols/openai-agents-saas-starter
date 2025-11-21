"""SQLAlchemy-backed session store implementing the provider port."""

from __future__ import annotations

from typing import Final

from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain.ai.ports import AgentSessionStore

SESSION_TABLE_NAME: Final[str] = "sdk_agent_sessions"
SESSION_MESSAGES_TABLE_NAME: Final[str] = "sdk_agent_session_messages"


class OpenAISQLAlchemySessionStore(AgentSessionStore):
    """Creates SQLAlchemySession handles for the OpenAI Agents SDK."""

    def __init__(
        self,
        engine: AsyncEngine,
        *,
        auto_create_tables: bool | None = None,
    ) -> None:
        self._engine = engine
        if auto_create_tables is None:
            auto_create_tables = engine.dialect.name.startswith("sqlite")
        self._auto_create_tables = auto_create_tables

    def build(self, session_id: str) -> SQLAlchemySession:
        return SQLAlchemySession(
            session_id=session_id,
            engine=self._engine,
            sessions_table=SESSION_TABLE_NAME,
            messages_table=SESSION_MESSAGES_TABLE_NAME,
            create_tables=self._auto_create_tables,
        )


__all__ = ["OpenAISQLAlchemySessionStore", "SESSION_TABLE_NAME", "SESSION_MESSAGES_TABLE_NAME"]
