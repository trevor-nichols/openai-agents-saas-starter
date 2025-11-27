from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.agents._shared.registry_loader import load_agent_specs
from app.domain.ai import AgentRunResult
from app.domain.ai.models import AgentStreamEvent
from app.services.agents.context import ConversationActorContext
from app.services.agents.provider_registry import get_provider_registry
from app.workflows.registry import WorkflowRegistry
from app.services.workflows.runner import WorkflowRunner
from app.workflows.specs import WorkflowSpec, WorkflowStep


class _FakeStreamHandle:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.last_response_id = "resp-1"
        self.usage = None

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        yield AgentStreamEvent(
            kind="run_item",
            response_id=self.last_response_id,
            response_text=self._response_text,
            is_terminal=True,
        )


class _FakeRuntime:
    async def run(self, agent_key: str, message: str, **_: Any) -> AgentRunResult:  # pragma: no cover - simple stub
        return AgentRunResult(final_output=f"{agent_key}:{message}", response_text=f"{agent_key}:{message}")

    def run_stream(self, agent_key: str, message: str, **_: Any) -> _FakeStreamHandle:  # pragma: no cover - simple stub
        return _FakeStreamHandle(f"{agent_key}:{message}")


def _actor() -> ConversationActorContext:
    return ConversationActorContext(tenant_id="t", user_id="u")


def test_registry_rejects_unknown_agent():
    specs = [WorkflowSpec(key="bad", display_name="Bad", description="", steps=(WorkflowStep(agent_key="missing"),))]
    with pytest.raises(ValueError):
        WorkflowRegistry(workflow_specs=specs, agent_specs=load_agent_specs())


def test_registry_rejects_handoff_when_disallowed():
    specs = [
        WorkflowSpec(
            key="no_handoff",
            display_name="No",
            description="",
            steps=(WorkflowStep(agent_key="triage"),),
            allow_handoff_agents=False,
        )
    ]
    with pytest.raises(ValueError):
        WorkflowRegistry(workflow_specs=specs, agent_specs=load_agent_specs())


@pytest.mark.asyncio
async def test_runner_sync_applies_guards_and_mappers(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    def guard(current_input, prior_steps):
        return "go" in str(current_input)

    def mapper(current_input, prior_steps):
        return f"mapped-{current_input}-{len(prior_steps)}"

    spec = WorkflowSpec(
        key="demo",
        display_name="Demo",
        description="",
        steps=(
            WorkflowStep(agent_key="code_assistant", name="first"),
            WorkflowStep(
                agent_key="data_analyst",
                name="second",
                guard="tests.unit.workflows.test_registry_runner:guard",
                input_mapper="tests.unit.workflows.test_registry_runner:mapper",
            ),
        ),
        allow_handoff_agents=True,
    )

    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", _FakeRuntime())

    try:
        result = await runner.run(
            spec,
            actor=_actor(),
            message="please go",
            conversation_id="c1",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert result.final_output == "data_analyst:mapped-code_assistant:please go-1"
    assert len(result.steps) == 2
    assert result.steps[0].response.response_text == "code_assistant:please go"
    assert result.steps[1].response.response_text == "data_analyst:mapped-code_assistant:please go-1"


@pytest.mark.asyncio
async def test_runner_stream_emits_metadata(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", _FakeRuntime())

    events: list[AgentStreamEvent] = []
    try:
        async for event in runner.run_stream(
            WorkflowSpec(
                key="demo_stream",
                display_name="Demo Stream",
                description="",
                steps=(WorkflowStep(agent_key="code_assistant"),),
                allow_handoff_agents=True,
            ),
            actor=_actor(),
            message="hello",
            conversation_id="c-stream",
        ):
            events.append(event)
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert events
    terminal = events[-1]
    assert terminal.is_terminal is True
    assert terminal.metadata and terminal.metadata.get("workflow_key") == "demo_stream"
    assert terminal.metadata.get("step_name") == "code_assistant"
    assert terminal.response_text == "code_assistant:hello"
