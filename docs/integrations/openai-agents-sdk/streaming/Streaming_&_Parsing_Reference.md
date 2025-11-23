OpenAI Agents SDK – Streaming & Parsing Reference
=================================================

This file documents the streaming events you see when using:

    result = Runner.run_streamed(...)

and iterating:

    async for event in result.stream_events():
        ...

Your own logging layer is already grouping these into:

    - raw_events     -> low-level Responses API events (TResponseStreamEvent)
    - run_items      -> high-level agent events (RunItemStreamEvent + RunItem)
    - agent_updates  -> agent change events (AgentUpdatedStreamEvent)

This file is a canonical reference for:

    1. All Agent streaming event wrappers (RawResponsesStreamEvent, RunItemStreamEvent,
       AgentUpdatedStreamEvent) – what you get from Agents SDK.
    2. All underlying Responses API streaming event types (`response.*` and `error`)
       – what lives inside `raw_events[*].type`.
    3. All RunItem types and how they map to run_item_stream_event.name / item.type.

You can keep this file in your codebase as “truth” for parsers, UI renderers, and tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Union, TypedDict, Protocol


# =============================================================================
# 1. Top-level Agents streaming events (what Runner.run_streamed() yields)
# =============================================================================

# In the Python Agents SDK:
#
#   StreamEvent = Union[
#       RawResponsesStreamEvent,
#       RunItemStreamEvent,
#       AgentUpdatedStreamEvent,
#   ]
#
# (JS adds AgentTextDeltaStreamEvent as a convenience; in Python you just use
# RawResponsesStreamEvent + ResponseTextDeltaEvent for text tokens.)

StreamEventType = Literal[
    "raw_response_event",
    "run_item_stream_event",
    "agent_updated_stream_event",
]

@dataclass
class RawResponsesStreamEvent:
    """
    A *raw* Responses API streaming event as returned by the underlying model.

    This is the ONLY place where token-level text deltas live in the Agents SDK.
    """

    type: Literal["raw_response_event"] = "raw_response_event"
    data: "ResponseStreamEvent" = None  # openai.types.responses.ResponseStreamEvent


@dataclass
class RunItemStreamEvent:
    """
    A higher-level, *semantic* event emitted by the Agents SDK when a RunItem
    has been fully generated (message, tool call, tool output, handoff, MCP, …).

    This is what you’re currently logging as `run_items`.
    """

    # name tells you *what* just happened at the agent level:
    name: Literal[
        "message_output_created",   # MessageOutputItem
        "handoff_requested",        # HandoffCallItem
        "handoff_occured",          # HandoffOutputItem (spelling kept for BC)
        "tool_called",              # ToolCallItem
        "tool_output",              # ToolCallOutputItem
        "reasoning_item_created",   # ReasoningItem
        "mcp_approval_requested",   # MCPApprovalRequestItem
        "mcp_approval_response",    # MCPApprovalResponseItem
        "mcp_list_tools",           # MCPListToolsItem
    ]

    # Concrete RunItem subclass instance (see RunItemType below)
    item: "RunItem"

    type: Literal["run_item_stream_event"] = "run_item_stream_event"


@dataclass
class AgentUpdatedStreamEvent:
    """
    Emitted whenever the *current agent* changes, typically due to a handoff.

        - new_agent: the Agent that is now active for the run loop
    """

    new_agent: "Agent"
    type: Literal["agent_updated_stream_event"] = "agent_updated_stream_event"


StreamEvent = Union[
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    AgentUpdatedStreamEvent,
]


# =============================================================================
# 2. Underlying Responses API streaming events (raw_events[*].type)
# =============================================================================
#
# This matches openai.types.responses.ResponseStreamEvent.type exactly.
# Only these strings will appear as event["type"] inside your `raw_events`.
#
# Grouped by function for readability; the union ResponseStreamEventType includes
# ALL of them.
# -----------------------------------------------------------------------------

# ---- 2.1 Lifecycle / response-level events ----------------------------------

ResponseLifecycleEventType = Literal[
    "response.created",      # initial envelope with id, model, etc.
    "response.queued",       # queued for processing (e.g., high load)
    "response.in_progress",  # model is actively generating / executing tools
    "response.completed",    # terminal, normal completion
    "response.incomplete",   # terminal, truncated (length, tool limit, etc.)
    "response.failed",       # terminal, failure at model or tool level
    "error",                 # non-typed error from server
]

# ---- 2.2 Output item & content part boundaries ------------------------------

ResponseItemEventType = Literal[
    "response.output_item.added",   # new item (message, tool call, etc.)
    "response.output_item.done",    # that item is fully done

    "response.content_part.added",  # new content part within an item
    "response.content_part.done",   # that content part finished
]

# ---- 2.3 Text streaming + annotations --------------------------------------

ResponseTextEventType = Literal[
    "response.output_text.delta",          # incremental text fragment
    "response.output_text.done",           # full text for that part
    "response.output_text.annotation.added",  # url_citation, file_citation, etc.
]

# ---- 2.4 Reasoning (o3 / gpt-5 reasoning traces) ----------------------------

ResponseReasoningEventType = Literal[
    # Reasoning summary is an internal structured trace.
    "response.reasoning_summary_part.added",
    "response.reasoning_summary_part.done",
    "response.reasoning_summary_text.delta",
    "response.reasoning_summary_text.done",

    # Reasoning “text” is the flattened reasoning content.
    "response.reasoning_text.delta",
    "response.reasoning_text.done",
]

# ---- 2.5 Refusals -----------------------------------------------------------

ResponseRefusalEventType = Literal[
    "response.refusal.delta",   # streaming refusal rationale
    "response.refusal.done",    # refusal summary finished
]

# ---- 2.6 Classic function calling ------------------------------------------

ResponseFunctionCallEventType = Literal[
    "response.function_call_arguments.delta",  # JSON args stream
    "response.function_call_arguments.done",   # full JSON args string
]

# ---- 2.7 Custom tool call input (generalized tools) ------------------------

ResponseCustomToolCallEventType = Literal[
    "response.custom_tool_call_input.delta",  # generalized tool-call args delta
    "response.custom_tool_call_input.done",   # args complete
]

# ---- 2.8 File search hosted tool -------------------------------------------

ResponseFileSearchEventType = Literal[
    "response.file_search_call.in_progress",
    "response.file_search_call.searching",
    "response.file_search_call.completed",
]

# ---- 2.9 Web search hosted tool --------------------------------------------

ResponseWebSearchEventType = Literal[
    "response.web_search_call.in_progress",
    "response.web_search_call.searching",
    "response.web_search_call.completed",
]

# ---- 2.10 Image generation hosted tool -------------------------------------

ResponseImageGenEventType = Literal[
    "response.image_generation_call.in_progress",
    "response.image_generation_call.generating",
    "response.image_generation_call.partial_image",  # intermediate preview
    "response.image_generation_call.completed",
]

# ---- 2.11 MCP (Model Context Protocol) tool calls --------------------------

ResponseMcpEventType = Literal[
    # A single MCP call
    "response.mcp_call_arguments.delta",
    "response.mcp_call_arguments.done",
    "response.mcp_call.in_progress",
    "response.mcp_call.completed",
    "response.mcp_call.failed",

    # Listing tools on an MCP server
    "response.mcp_list_tools.in_progress",
    "response.mcp_list_tools.completed",
    "response.mcp_list_tools.failed",
]

# ---- 2.12 Code interpreter hosted tool -------------------------------------

ResponseCodeInterpreterEventType = Literal[
    # The Python code text itself
    "response.code_interpreter_call_code.delta",
    "response.code_interpreter_call_code.done",

    # The call lifecycle
    "response.code_interpreter_call.in_progress",
    "response.code_interpreter_call.interpreting",
    "response.code_interpreter_call.completed",
]

# ---- 2.13 Audio (for realtime / voice) -------------------------------------

ResponseAudioEventType = Literal[
    "response.audio.delta",              # audio bytes / encoded fragment
    "response.audio.done",               # audio segment finished
    "response.audio.transcript.delta",   # transcript text delta
    "response.audio.transcript.done",    # full transcript for that segment
]

# ---- 2.14 Combined Responses event type ------------------------------------

ResponseStreamEventType = Literal[
    # Lifecycle
    *ResponseLifecycleEventType.__args__,
    # Items / parts
    *ResponseItemEventType.__args__,
    # Text & annotations
    *ResponseTextEventType.__args__,
    # Reasoning
    *ResponseReasoningEventType.__args__,
    # Refusals
    *ResponseRefusalEventType.__args__,
    # Tools
    *ResponseFunctionCallEventType.__args__,
    *ResponseCustomToolCallEventType.__args__,
    *ResponseFileSearchEventType.__args__,
    *ResponseWebSearchEventType.__args__,
    *ResponseImageGenEventType.__args__,
    *ResponseMcpEventType.__args__,
    *ResponseCodeInterpreterEventType.__args__,
    # Audio
    *ResponseAudioEventType.__args__,
]

class ResponseStreamEvent(Protocol):
    """
    Shape of openai.types.responses.ResponseStreamEvent as far as parsing is
    concerned. In practice you’ll usually inspect .type and then pattern-match
    on the concrete subclass (ResponseTextDeltaEvent, ResponseOutputItemAddedEvent, …).
    """

    type: ResponseStreamEventType
    sequence_number: int


# =============================================================================
# 3. RunItems – high-level agent items (run_items[*])
# =============================================================================
#
# RunItem is a union of semantic “chunks” the Agents SDK derives from the
# raw Responses items. You normally see them via `RunItemStreamEvent`.
# -----------------------------------------------------------------------------

RunItemType = Literal[
    "message_output_item",
    "handoff_call_item",
    "handoff_output_item",
    "tool_call_item",
    "tool_call_output_item",
    "reasoning_item",
    "mcp_list_tools_item",
    "mcp_approval_request_item",
    "mcp_approval_response_item",
]

class RunItem(Protocol):
    """
    Base protocol for all RunItem subclasses.

    Real classes (from agents.items) include:

        - MessageOutputItem
        - HandoffCallItem
        - HandoffOutputItem
        - ToolCallItem
        - ToolCallOutputItem
        - ReasoningItem
        - MCPListToolsItem
        - MCPApprovalRequestItem
        - MCPApprovalResponseItem
    """

    type: RunItemType
    raw_item: Any        # underlying ResponseOutputItem / tool call / input item
    agent: "Agent"       # agent whose run produced this item


# Mapping between RunItemStreamEvent.name and item.type for clarity:

RUN_ITEM_EVENT_TO_ITEM_TYPE = {
    "message_output_created":  "message_output_item",
    "handoff_requested":       "handoff_call_item",
    "handoff_occured":         "handoff_output_item",   # spelling preserved by SDK
    "tool_called":             "tool_call_item",
    "tool_output":             "tool_call_output_item",
    "reasoning_item_created":  "reasoning_item",
    "mcp_list_tools":          "mcp_list_tools_item",
    "mcp_approval_requested":  "mcp_approval_request_item",
    "mcp_approval_response":   "mcp_approval_response_item",
}


# =============================================================================
# 4. How this maps to your logging schema
# =============================================================================
#
# Given a streaming run:
#
#     result = Runner.run_streamed(agent, input=...)
#
# You can populate your JSON like the example you posted as:
#
#     timestamp: ISO8601
#     agent:     current_agent.name
#
#     raw_events: [
#         {
#             "type":   event.data.type,
#             "sequence_number": event.data.sequence_number,
#             ... full event.data.model_dump()
#         }
#         for event in result.stream_events()
#         if event.type == "raw_response_event"
#     ]
#
#     run_items: [
#         {
#             "event_type": "run_item_stream_event",
#             "name":       event.name,
#             "item_type":  event.item.type,
#             # You can JSON-ify via dataclasses.asdict(event.item) or .model_dump()
#             "item":       repr(event.item),
#         }
#         for event in result.stream_events()
#         if event.type == "run_item_stream_event"
#     ]
#
#     agent_updates: [
#         {
#             "event_type": "agent_updated_stream_event",
#             "agent_name": event.new_agent.name,
#             "event":      repr(event),
#         }
#         for event in result.stream_events()
#         if event.type == "agent_updated_stream_event"
#     ]
#
#     final_output: result.final_output
#
# On top of this, parsers can:
#
#   - UI typing effect:
#       Use RawResponsesStreamEvent where data.type == "response.output_text.delta"
#       and accumulate data.delta.
#
#   - Tool call playback:
#       Either:
#         - use raw_events:
#             - function tools:      response.function_call_arguments.*
#             - hosted tools:        response.file_search_call.*, response.web_search_call.*,
#                                   response.image_generation_call.*, response.mcp_call.*,...
#         - or the higher-level:
#             - RunItemStreamEvent where name in {"tool_called", "tool_output"}
#
#   - Reasoning trace:
#       Filter raw_events for:
#           response.reasoning_text.delta/done
#           response.reasoning_summary_*.*   (if you want summaries)
#
#   - Agent handoffs & routing:
#       - RunItemStreamEvent with name "handoff_requested" / "handoff_occured"
#       - AgentUpdatedStreamEvent whenever current agent changes
#
# This file can be treated as the canonical “event taxonomy” for your platform.

