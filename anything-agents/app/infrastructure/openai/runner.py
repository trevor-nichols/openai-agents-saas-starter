"""Wrapper helpers around the OpenAI Agents SDK runner."""

from agents import Agent, Runner


async def run(agent: Agent, agent_input: str):
    """Execute an agent interaction and return the Runner result."""

    return await Runner.run(agent, agent_input)


def run_streamed(agent: Agent, agent_input: str):
    """Execute an agent interaction and return the streaming handle."""

    return Runner.run_streamed(agent, agent_input)
