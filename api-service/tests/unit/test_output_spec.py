import pytest
from pydantic import BaseModel

from agents.agent_output import AgentOutputSchema, AgentOutputSchemaBase

from app.agents._shared.specs import AgentSpec, OutputSpec
from app.infrastructure.providers.openai.registry import OpenAIAgentRegistry
from app.infrastructure.providers.openai.runtime import OpenAIStreamingHandle
from app.core.settings import Settings


class ExampleModel(BaseModel):
    message: str


class ExampleCustomSchema(AgentOutputSchemaBase):
    def is_plain_text(self) -> bool:
        return False

    def name(self) -> str:
        return "example_custom"

    def json_schema(self) -> dict[str, object]:
        return {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}

    def is_strict_json_schema(self) -> bool:
        return False

    def validate_json(self, json_str: str) -> dict[str, str]:
        return {"validated": json_str}


async def _noop_searcher(tenant_id: str, query: str):
    return []


def _make_registry(spec: AgentSpec) -> OpenAIAgentRegistry:
    return OpenAIAgentRegistry(
        settings_factory=lambda: Settings(),
        conversation_searcher=_noop_searcher,
        specs=[spec],
    )


def test_output_spec_strict_json_schema():
    spec = AgentSpec(
        key="strict_agent",
        display_name="Strict Agent",
        description="Strict schema agent",
        instructions="hi",
        output=OutputSpec(
            mode="json_schema",
            type_path="tests.unit.test_output_spec:ExampleModel",
            strict=True,
        ),
    )
    registry = _make_registry(spec)

    agent = registry.get_agent_handle("strict_agent", validate_prompts=False)
    assert isinstance(agent.output_type, AgentOutputSchema)
    assert agent.output_type.is_strict_json_schema() is True


def test_output_spec_non_strict_json_schema():
    spec = AgentSpec(
        key="non_strict_agent",
        display_name="Non-strict Agent",
        description="Non-strict schema agent",
        instructions="hi",
        output=OutputSpec(
            mode="json_schema",
            type_path="tests.unit.test_output_spec:ExampleModel",
            strict=False,
        ),
    )
    registry = _make_registry(spec)

    agent = registry.get_agent_handle("non_strict_agent", validate_prompts=False)
    assert isinstance(agent.output_type, AgentOutputSchema)
    assert agent.output_type.is_strict_json_schema() is False


def test_output_spec_custom_schema():
    spec = AgentSpec(
        key="custom_schema_agent",
        display_name="Custom Schema Agent",
        description="Custom schema agent",
        instructions="hi",
        output=OutputSpec(
            mode="json_schema",
            custom_schema_path="tests.unit.test_output_spec:ExampleCustomSchema",
        ),
    )
    registry = _make_registry(spec)

    agent = registry.get_agent_handle("custom_schema_agent", validate_prompts=False)
    assert isinstance(agent.output_type, ExampleCustomSchema)


@pytest.mark.asyncio
async def test_streaming_emits_structured_output_event():
    class FakeRaw:
        def __init__(self, raw_type: str):
            self.type = raw_type
            self.sequence_number = 1
            self.delta = None

    class FakeEvent:
        def __init__(self, event_type: str, data=None, item=None, name=None):
            self.type = event_type
            self.data = data
            self.item = item
            self.name = name

    class FakeStream:
        def __init__(self):
            self.final_output = {"message": "hi"}
            self.last_response_id = "resp_123"
            self.context_wrapper = type("ctx", (), {"usage": None})

        async def stream_events(self):
            yield FakeEvent("raw_response_event", FakeRaw("response.completed"))

    handle = OpenAIStreamingHandle(
        stream=FakeStream(),
        agent_key="agent_x",
        metadata={"agent_key": "agent_x"},
    )

    events = [ev async for ev in handle.events()]

    assert len(events) == 2
    raw, final = events
    assert raw.kind == "raw_response"
    assert raw.is_terminal is False

    assert final.kind == "run_item"
    assert final.is_terminal is True
    assert final.structured_output == {"message": "hi"}
    assert final.response_text == '{"message": "hi"}'
