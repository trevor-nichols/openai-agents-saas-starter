"""Factory helpers for OpenAI Agents SDK SQLAlchemy-backed sessions."""

from __future__ import annotations

from typing import Final

from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import AsyncEngine

SESSION_TABLE_NAME: Final[str] = "sdk_agent_sessions"
SESSION_MESSAGES_TABLE_NAME: Final[str] = "sdk_agent_session_messages"

_session_engine: AsyncEngine | None = None
_auto_create_tables: bool = False


def configure_sdk_session_store(
    engine: AsyncEngine, *, auto_create_tables: bool | None = None
) -> None:
    """Set the AsyncEngine used by SDK sessions."""

    global _session_engine, _auto_create_tables
    _session_engine = engine
    if auto_create_tables is None:
        _auto_create_tables = engine.dialect.name.startswith("sqlite")
    else:
        _auto_create_tables = auto_create_tables


def reset_sdk_session_store() -> None:
    """Reset the configured engine (primarily for tests)."""

    global _session_engine, _auto_create_tables
    _session_engine = None
    _auto_create_tables = False


def build_conversation_session(session_id: str) -> SQLAlchemySession:
    """Construct a SQLAlchemySession for the given conversation."""

    if _session_engine is None:
        raise RuntimeError("SDK session store has not been configured.")

    return SQLAlchemySession(
        session_id=session_id,
        engine=_session_engine,
        sessions_table=SESSION_TABLE_NAME,
        messages_table=SESSION_MESSAGES_TABLE_NAME,
        create_tables=_auto_create_tables,
    )
