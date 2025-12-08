from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.domain.ai import AgentRunResult
from app.domain.ai.models import AgentStreamEvent
from app.services.workflows.runner import WorkflowRunner
from app.workflows._shared.specs import WorkflowSpec, WorkflowStep
from app.workflows._shared.registry import WorkflowRegistry
from app.services.agents.context import ConversationActorContext
from app.services.agents.provider_registry import get_provider_registry
from app.services.agents.interaction_context import InteractionContextBuilder
from app.workflows._shared.specs import WorkflowStage


class _MultiStepFakeStream:
    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = responses
        self.last_response_id = "resp"
        self.usage = None

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        for idx, payload in enumerate(self._responses):
            yield AgentStreamEvent(
                kind="run_item_stream_event",
                response_id=self.last_response_id,
                response_text=payload.get("text"),
                structured_output=payload.get("structured"),
                is_terminal=payload.get("terminal", False),
                sequence_number=idx,
            )


class _FakeRuntime:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def run(self, agent_key: str, message: str, **_: Any):
        self.calls.append((agent_key, message))
        if agent_key == "a1":
            return AgentRunResult(final_output={"foo": "bar"}, structured_output={"foo": "bar"})
        return AgentRunResult(final_output={"foo": "bar"}, structured_output={"foo": "bar"})

    def run_stream(self, agent_key: str, message: str, **_: Any):  # pragma: no cover - simple stub
        self.calls.append((agent_key, message))
        # First agent emits text, second emits structured only
        if agent_key == "a1":
            return _MultiStepFakeStream(
                [
                    {"text": "step1", "terminal": True},
                ]
            )
        return _MultiStepFakeStream(
            [
                {"structured": {"foo": "bar"}},
                {"structured": {"foo": "bar"}, "terminal": True},
            ]
        )


def _concat(outputs, _prior):
    return "|".join(str(o) for o in outputs if o is not None)


class _ParallelRuntime(_FakeRuntime):
    def run_stream(self, agent_key: str, message: str, **_: Any):  # pragma: no cover - simple stub
        self.calls.append((agent_key, message))
        # Emit a single terminal event carrying the response text
        return _MultiStepFakeStream(
            [
                {"text": f"{agent_key}:{message}", "terminal": True},
            ]
        )


class _ErrorRuntime(_FakeRuntime):
    def run_stream(self, agent_key: str, message: str, **_: Any):  # pragma: no cover - simple stub
        raise RuntimeError("stream boom")


@pytest.mark.asyncio
async def test_streaming_multi_step_and_structured_propagates():
    registry = WorkflowRegistry()
    fake_runtime = _FakeRuntime()
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", fake_runtime)

    runner = WorkflowRunner(
        registry=registry,
        interaction_builder=InteractionContextBuilder(),
    )

    spec = WorkflowSpec(
        key="stream-demo",
        display_name="Stream Demo",
        description="",
        steps=(WorkflowStep(agent_key="a1"), WorkflowStep(agent_key="a2")),
        allow_handoff_agents=True,
    )

    events: list[AgentStreamEvent] = []
    try:
        async for ev in runner.run_stream(
            spec,
            actor=ConversationActorContext(tenant_id="t", user_id="u"),
            message="start",
            conversation_id="c",
        ):
            events.append(ev)
    finally:
        setattr(provider, "_runtime", original_runtime)

    # Should have streamed both steps (last event terminal from second step)
    assert events and events[-1].is_terminal
    assert fake_runtime.calls == [("a1", "start"), ("a2", "step1")]

    # Structured-only output from second step propagated into final event
    structured_seen = [e.structured_output for e in events if e.structured_output]
    assert structured_seen[-1] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_sync_propagates_structured_between_steps():
    registry = WorkflowRegistry()
    fake_runtime = _FakeRuntime()
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", fake_runtime)

    runner = WorkflowRunner(
        registry=registry,
        interaction_builder=InteractionContextBuilder(),
    )

    spec = WorkflowSpec(
        key="sync-demo",
        display_name="Sync Demo",
        description="",
        steps=(WorkflowStep(agent_key="a1"), WorkflowStep(agent_key="a2")),
        allow_handoff_agents=True,
    )

    try:
        result = await runner.run(
            spec,
            actor=ConversationActorContext(tenant_id="t", user_id="u"),
            message="start",
            conversation_id="c",
        )
    finally:
        setattr(provider, "_runtime", original_runtime)

    assert fake_runtime.calls == [("a1", "start"), ("a2", {"foo": "bar"})]
    assert result.final_output == {"foo": "bar"}
    assert result.steps[-1].response.structured_output == {"foo": "bar"}


@pytest.mark.asyncio
async def test_stream_parallel_stage_streams_with_metadata():
    registry = WorkflowRegistry()
    fake_runtime = _ParallelRuntime()
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", fake_runtime)

    runner = WorkflowRunner(
        registry=registry,
        interaction_builder=InteractionContextBuilder(),
    )

    spec = WorkflowSpec(
        key="stream-parallel",
        display_name="Stream Parallel",
        description="",
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(
                    WorkflowStep(agent_key="a1", name="left"),
                    WorkflowStep(agent_key="a2", name="right"),
                ),
                reducer="tests.unit.workflows.test_streaming_regressions:_concat",
            ),
            WorkflowStage(
                name="synthesis",
                steps=(WorkflowStep(agent_key="a3", name="synth"),),
            ),
        ),
        allow_handoff_agents=True,
    )

    events: list[AgentStreamEvent] = []
    try:
        async for ev in runner.run_stream(
            spec,
            actor=ConversationActorContext(tenant_id="t", user_id="u"),
            message="prompt",
            conversation_id="c",
        ):
            events.append(ev)
    finally:
        setattr(provider, "_runtime", original_runtime)

    # We expect 3 terminal events (two branches + synthesis), but order is not guaranteed for the first two.
    branch_events = [e for e in events if e.metadata and e.metadata.get("parallel_group")]
    assert branch_events, "parallel branch events should be present"
    for idx, ev in enumerate(branch_events):
        meta = ev.metadata or {}
        assert meta.get("stage_name") == "fanout"
        assert meta.get("parallel_group") == "fanout"
        assert meta.get("branch_index") in (0, 1)

    # Synthesis call should receive reduced input "a1:prompt|a2:prompt"
    assert fake_runtime.calls[-1] == ("a3", "a1:prompt|a2:prompt")
    assert events[-1].is_terminal is True


@pytest.mark.asyncio
async def test_stream_parallel_branch_error_surfaces_and_does_not_hang():
    registry = WorkflowRegistry()
    err_runtime = _ErrorRuntime()
    provider = get_provider_registry().get_default()
    original_runtime = getattr(provider, "_runtime", None)
    setattr(provider, "_runtime", err_runtime)

    runner = WorkflowRunner(
        registry=registry,
        interaction_builder=InteractionContextBuilder(),
    )

    spec = WorkflowSpec(
        key="stream-parallel-error",
        display_name="Stream Parallel Error",
        description="",
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(WorkflowStep(agent_key="a1", name="left"),),
                reducer="tests.unit.workflows.test_streaming_regressions:_concat",
            ),
        ),
        allow_handoff_agents=True,
    )

    with pytest.raises(RuntimeError, match="stream boom"):
        async for _ in runner.run_stream(
            spec,
            actor=ConversationActorContext(tenant_id="t", user_id="u"),
            message="prompt",
            conversation_id="c",
        ):
            # Should raise before yielding anything
            pass
    setattr(provider, "_runtime", original_runtime)
