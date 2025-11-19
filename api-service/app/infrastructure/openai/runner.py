"""Wrapper helpers around the OpenAI Agents SDK runner."""

from __future__ import annotations

from typing import Any

from agents import Agent, Runner
from agents.memory.session import Session


async def run(
    agent: Agent,
    agent_input: str,
    *,
    conversation_id: str | None = None,
    session: Session | None = None,
    **kwargs: Any,
):
    """Execute an agent interaction and return the Runner result."""

    return await Runner.run(
        agent,
        agent_input,
        conversation_id=conversation_id,
        session=session,
        **kwargs,
    )


def run_streamed(
    agent: Agent,
    agent_input: str,
    *,
    conversation_id: str | None = None,
    session: Session | None = None,
    **kwargs: Any,
):
    """Execute an agent interaction and return the streaming handle."""

    return Runner.run_streamed(
        agent,
        agent_input,
        conversation_id=conversation_id,
        session=session,
        **kwargs,
    )
