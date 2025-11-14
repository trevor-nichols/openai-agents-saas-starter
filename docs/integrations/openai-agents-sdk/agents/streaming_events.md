Streaming events
StreamEvent module-attribute

StreamEvent: TypeAlias = Union[
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    AgentUpdatedStreamEvent,
]
A streaming event from an agent.

RawResponsesStreamEvent dataclass
Streaming event from the LLM. These are 'raw' events, i.e. they are directly passed through from the LLM.

Source code in src/agents/stream_events.py
data instance-attribute

data: TResponseStreamEvent
The raw responses streaming event from the LLM.

type class-attribute instance-attribute

type: Literal['raw_response_event'] = 'raw_response_event'
The type of the event.

RunItemStreamEvent dataclass
Streaming events that wrap a RunItem. As the agent processes the LLM response, it will generate these events for new messages, tool calls, tool outputs, handoffs, etc.

Source code in src/agents/stream_events.py
name instance-attribute

name: Literal[
    "message_output_created",
    "handoff_requested",
    "handoff_occured",
    "tool_called",
    "tool_output",
    "reasoning_item_created",
    "mcp_approval_requested",
    "mcp_list_tools",
]
The name of the event.

item instance-attribute

item: RunItem
The item that was created.

AgentUpdatedStreamEvent dataclass
Event that notifies that there is a new agent running.

Source code in src/agents/stream_events.py
new_agent instance-attribute

new_agent: Agent[Any]
The new agent.

