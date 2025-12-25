import pytest

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.infrastructure.providers.openai.runtime import (
    OpenAIAgentRuntime,
    OpenAIStreamingHandle,
)


class _DummyRegistry:
    def __init__(self, agent):
        self.agent = agent
        self.seen_runtime_ctx = None

    def get_agent_handle(
        self, agent_key, *, runtime_ctx=None, validate_prompts=True, tool_stream_bus=None
    ):
        self.seen_runtime_ctx = runtime_ctx
        return self.agent

    def get_code_interpreter_mode(self, agent_key):  # pragma: no cover - simple stub
        _ = agent_key
        return None

    def get_agent_tool_names(self, agent_key):  # pragma: no cover - simple stub
        _ = agent_key
        return []


class _DummyAgent:
    def __init__(self, model: str):
        self.model = model


@pytest.mark.asyncio
async def test_runtime_strips_prompt_ctx_from_metadata(monkeypatch):
    agent = _DummyAgent(model="dummy-model")
    registry = _DummyRegistry(agent)
    runtime = OpenAIAgentRuntime(registry)

    async def fake_run(agent_obj, message, session=None, conversation_id=None, **kwargs):
        class _Result:
            usage = None
            response_id = "resp-1"
            final_output = "ok"

        return _Result()

    monkeypatch.setattr("app.infrastructure.providers.openai.runtime.Runner.run", fake_run)

    prompt_ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="conv-1",
        request_message="hi",
        settings=None,
    )
    result = await runtime.run(
        agent_key="triage",
        message="hi",
        metadata={"prompt_runtime_ctx": prompt_ctx, "trace_id": "t123"},
    )

    assert registry.seen_runtime_ctx is prompt_ctx
    assert result.metadata == {
        "agent_key": "triage",
        "model": "dummy-model",
        "trace_id": "t123",
    }


@pytest.mark.asyncio
async def test_runtime_bootstraps_prompt_ctx_when_missing(monkeypatch):
    agent = _DummyAgent(model="dummy-model")
    registry = _DummyRegistry(agent)
    runtime = OpenAIAgentRuntime(registry)

    async def fake_run(agent_obj, message, session=None, conversation_id=None, **kwargs):
        class _Result:
            usage = None
            response_id = "resp-1"
            final_output = "ok"

        return _Result()

    monkeypatch.setattr("app.infrastructure.providers.openai.runtime.Runner.run", fake_run)

    result = await runtime.run(agent_key="triage", message="hi", metadata=None)

    assert registry.seen_runtime_ctx is not None
    assert registry.seen_runtime_ctx.conversation_id == "bootstrap"
    assert result.metadata == {
        "agent_key": "triage",
        "model": "dummy-model",
    }


@pytest.mark.asyncio
async def test_run_stream_strips_prompt_ctx(monkeypatch):
    agent = _DummyAgent(model="dummy-model")
    registry = _DummyRegistry(agent)
    runtime = OpenAIAgentRuntime(registry)

    class _Stream:
        async def stream_events(self):
            if False:
                yield None

    def fake_run_streamed(agent_obj, message, session=None, conversation_id=None, **kwargs):
        return _Stream()

    monkeypatch.setattr(
        "app.infrastructure.providers.openai.runtime.Runner.run_streamed",
        fake_run_streamed,
    )

    prompt_ctx = PromptRuntimeContext(
        actor=None,
        conversation_id="conv-1",
        request_message="hi",
        settings=None,
    )
    handle = runtime.run_stream(
        agent_key="triage",
        message="hi",
        metadata={"prompt_runtime_ctx": prompt_ctx, "trace_id": "t123"},
    )

    # runtime_ctx should be passed through
    assert registry.seen_runtime_ctx is prompt_ctx
    assert isinstance(handle, OpenAIStreamingHandle)
    assert handle.metadata == {
        "agent_key": "triage",
        "model": "dummy-model",
        "trace_id": "t123",
    }
