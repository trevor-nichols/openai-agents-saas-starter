from __future__ import annotations

import types
from typing import Any

import pytest
from agents import Agent, Runner
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from app.domain.ai import AgentRunResult, RunOptions
from app.infrastructure.providers.openai.runtime import OpenAIAgentRuntime


class DummyRegistry:
    def __init__(self) -> None:
        self._agent = Agent(name="Test", instructions=prompt_with_handoff_instructions("hi"))

    def get_agent_handle(self, agent_key: str, *, runtime_ctx=None, validate_prompts: bool = True):
        return self._agent

    @property
    def default_agent_key(self) -> str:  # pragma: no cover - not used
        return "test"


class FakeStream:
    def __init__(self):
        self.last_response_id = "resp-123"
        self.context_wrapper = types.SimpleNamespace(usage=None)

    async def stream_events(self):
        yield types.SimpleNamespace(type="raw_response_event", data=None)


@pytest.mark.asyncio
async def test_runtime_passes_runconfig_and_previous_id(monkeypatch: pytest.MonkeyPatch):
    calls: dict[str, Any] = {}

    async def fake_run(agent, message, **kwargs):
        calls.update(kwargs)
        return AgentRunResult(final_output="ok", response_id="r1", usage=None)

    monkeypatch.setattr(Runner, "run", fake_run)
    runtime = OpenAIAgentRuntime(DummyRegistry())

    await runtime.run(
        "test",
        "hello",
        options=RunOptions(
            previous_response_id="prev-xyz",
            max_turns=5,
            handoff_input_filter="fresh",
            run_config={"tracing_disabled": True},
        ),
    )

    assert calls["previous_response_id"] == "prev-xyz"
    assert calls["max_turns"] == 5
    rc = calls["run_config"]
    assert rc.tracing_disabled is True
    # global handoff filter
    assert rc.handoff_input_filter is not None


@pytest.mark.asyncio
async def test_runtime_stream_includes_hooks(monkeypatch: pytest.MonkeyPatch):
    calls: dict[str, Any] = {}

    def fake_run_streamed(agent, message, **kwargs):
        calls.update(kwargs)
        return FakeStream()

    monkeypatch.setattr(Runner, "run_streamed", fake_run_streamed)
    runtime = OpenAIAgentRuntime(DummyRegistry())

    handle = runtime.run_stream(
        "test",
        "hello",
        options=RunOptions(
            handoff_input_filter="last_turn",
        ),
    )

    assert calls["run_config"].handoff_input_filter is not None
    # hooks are provided
    assert calls["hooks"] is not None
    # streaming handle still works
    events = []
    async for evt in handle.events():
        events.append(evt)
    assert events  # at least one event forwarded

