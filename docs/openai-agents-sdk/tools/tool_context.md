Tool Context
ToolContext dataclass
Bases: RunContextWrapper[TContext]

The context of a tool call.

Source code in src/agents/tool_context.py
tool_name class-attribute instance-attribute

tool_name: str = field(
    default_factory=_assert_must_pass_tool_name
)
The name of the tool being invoked.

tool_call_id class-attribute instance-attribute

tool_call_id: str = field(
    default_factory=_assert_must_pass_tool_call_id
)
The ID of the tool call.

context instance-attribute

context: TContext
The context object (or None), passed by you to Runner.run()

usage class-attribute instance-attribute

usage: Usage = field(default_factory=Usage)
The usage of the agent run so far. For streamed responses, the usage will be stale until the last chunk of the stream is processed.

from_agent_context classmethod

from_agent_context(
    context: RunContextWrapper[TContext],
    tool_call_id: str,
    tool_call: Optional[ResponseFunctionToolCall] = None,
) -> ToolContext
Create a ToolContext from a RunContextWrapper.

Source code in src/agents/tool_context.py
