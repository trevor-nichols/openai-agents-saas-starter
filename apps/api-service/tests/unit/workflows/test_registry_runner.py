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
from app.workflows.specs import WorkflowSpec, WorkflowStep, WorkflowStage


class _FakeStreamHandle:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.last_response_id = "resp-1"
        self.usage = None

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        yield AgentStreamEvent(
            kind="run_item_stream_event",
            response_id=self.last_response_id,
            response_text=self._response_text,
            is_terminal=True,
        )


class _FakeRuntime:
    def __init__(self):
        self.calls: list[tuple[str, Any]] = []

    async def run(self, agent_key: str, message: Any, **_: Any) -> AgentRunResult:  # pragma: no cover - simple stub
        self.calls.append((agent_key, message))
        return AgentRunResult(final_output=f"{agent_key}:{message}", response_text=f"{agent_key}:{message}")

    def run_stream(self, agent_key: str, message: Any, **_: Any) -> _FakeStreamHandle:  # pragma: no cover - simple stub
        self.calls.append((agent_key, message))
        return _FakeStreamHandle(f"{agent_key}:{message}")


def _actor() -> ConversationActorContext:
    return ConversationActorContext(tenant_id="t", user_id="u")


def guard(current_input, _prior_steps):
    return "go" in str(current_input)


def mapper(current_input, prior_steps):
    return f"mapped-{current_input}-{len(prior_steps)}"


def reducer(outputs, _prior):
    return "|".join(str(o) for o in outputs if o is not None)


def reducer_raises(outputs, _prior):
    raise RuntimeError("boom")


def guard_false(_current, _prior):
    return False


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
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

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
async def test_runner_parallel_stage_executes_in_parallel(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    spec = WorkflowSpec(
        key="parallel-demo",
        display_name="Parallel",
        description="",
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(
                    WorkflowStep(agent_key="code_assistant", name="code"),
                    WorkflowStep(agent_key="data_analyst", name="analysis"),
                ),
                reducer="tests.unit.workflows.test_registry_runner:reducer",
            ),
            WorkflowStage(
                name="synthesis",
                steps=(WorkflowStep(agent_key="code_assistant", name="synthesis"),),
            ),
        ),
        allow_handoff_agents=True,
    )

    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

    try:
        result = await runner.run(
            spec,
            actor=_actor(),
            message="prompt",
            conversation_id="conv",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    calls = fake_runtime.calls
    assert len(calls) == 3
    # Fanout receives original input
    assert ("code_assistant", "prompt") in calls
    assert ("data_analyst", "prompt") in calls
    # Synthesis receives reducer output
    assert calls[-1][1] == "code_assistant:prompt|data_analyst:prompt"
    assert result.steps[-1].stage_name == "synthesis"
    assert result.final_output == f"code_assistant:{calls[-1][1]}"


@pytest.mark.asyncio
async def test_runner_parallel_reducer_failure_bubbles(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    spec = WorkflowSpec(
        key="parallel-fail",
        display_name="Parallel Fail",
        description="",
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(
                    WorkflowStep(agent_key="code_assistant", name="code"),
                    WorkflowStep(agent_key="data_analyst", name="analysis"),
                ),
                reducer="tests.unit.workflows.test_registry_runner:reducer_raises",
            ),
        ),
        allow_handoff_agents=True,
    )

    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

    try:
        with pytest.raises(RuntimeError, match="boom"):
            await runner.run(
                spec,
                actor=_actor(),
                message="prompt",
                conversation_id="conv",
            )
    finally:
        setattr(provider, "_runtime", original_runtime)


@pytest.mark.asyncio
async def test_runner_parallel_all_guards_skipped_preserves_input(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    spec = WorkflowSpec(
        key="parallel-skip",
        display_name="Parallel Skip",
        description="",
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(
                    WorkflowStep(
                        agent_key="code_assistant",
                        name="code",
                        guard="tests.unit.workflows.test_registry_runner:guard_false",
                    ),
                    WorkflowStep(
                        agent_key="data_analyst",
                        name="analysis",
                        guard="tests.unit.workflows.test_registry_runner:guard_false",
                    ),
                ),
            ),
            WorkflowStage(
                name="synthesis",
                steps=(WorkflowStep(agent_key="code_assistant", name="synth"),),
            ),
        ),
        allow_handoff_agents=True,
    )

    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    fake_runtime = _FakeRuntime()
    setattr(provider, "_runtime", fake_runtime)

    try:
        result = await runner.run(
            spec,
            actor=_actor(),
            message="keep-me",
            conversation_id="conv",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    calls = fake_runtime.calls
    assert ("code_assistant", "keep-me") in calls  # synthesis step saw original input
    # Fanout steps were skipped, so only synthesis should have run.
    assert len(calls) == 1
    assert result.final_output == "code_assistant:keep-me"


@pytest.mark.asyncio
async def test_runner_all_steps_guarded_results_in_none_final_output(monkeypatch: pytest.MonkeyPatch):
    registry = WorkflowRegistry()
    runner = WorkflowRunner(registry=registry)

    spec = WorkflowSpec(
        key="all-guarded",
        display_name="All Guarded",
        description="",
        stages=(
            WorkflowStage(
                name="only",
                steps=(
                    WorkflowStep(
                        agent_key="code_assistant",
                        name="code",
                        guard="tests.unit.workflows.test_registry_runner:guard_false",
                    ),
                ),
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
            message="prompt",
            conversation_id="conv",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert result.steps == []
    assert result.final_output is None


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
