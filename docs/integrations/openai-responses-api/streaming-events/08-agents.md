# OpenAI Agents Sdk - Streaming events

## `StreamEvent`
*module-attribute*

```python
StreamEvent: TypeAlias = Union[
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    AgentUpdatedStreamEvent,
]
```
A streaming event from an agent.

---

## `RawResponsesStreamEvent`
*dataclass*

Streaming event from the LLM. These are 'raw' events, i.e. they are directly passed through from the LLM.

> Source code in `src/agents/stream_events.py`

### Attributes

*   **data**
    *   Type: `TResponseStreamEvent`
    *   The raw responses streaming event from the LLM.

*   **type**
    *   Type: `Literal['raw_response_event'] = 'raw_response_event'`
    *   The type of the event.

---

## `RunItemStreamEvent`
*dataclass*

Streaming events that wrap a RunItem. As the agent processes the LLM response, it will generate these events for new messages, tool calls, tool outputs, handoffs, etc.

> Source code in `src/agents/stream_events.py`

### Attributes

*   **name**
    *   Type:
        ```python
        Literal[
            "message_output_created",
            "handoff_requested",
            "handoff_occured",
            "tool_called",
            "tool_output",
            "reasoning_item_created",
            "mcp_approval_requested",
            "mcp_approval_response",
            "mcp_list_tools",
        ]
        ```
    *   The name of the event.

*   **item**
    *   Type: `RunItem`
    *   The item that was created.

---

## `AgentUpdatedStreamEvent`
*dataclass*

Event that notifies that there is a new agent running.

> Source code in `src/agents/stream_events.py`

### Attributes

*   **new_agent**
    *   Type: `Agent[Any]`