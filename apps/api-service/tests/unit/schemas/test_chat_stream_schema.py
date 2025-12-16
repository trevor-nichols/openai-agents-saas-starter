from app.api.v1.chat.schemas import StreamingChatEvent
from app.api.v1.shared.streaming import (
    CodeInterpreterTool,
    FileSearchTool,
    McpTool,
    ReasoningSummaryDeltaEvent,
    RefusalDoneEvent,
    ToolArgumentsDeltaEvent,
    ToolArgumentsDoneEvent,
    ToolCodeDoneEvent,
    ToolStatusEvent,
    WebSearchTool,
)


def test_streaming_chat_event_accepts_web_search_tool_status():
    parsed = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_1",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "tool.status",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "researcher",
            "tool": {
                "tool_type": "web_search",
                "tool_call_id": "ws_1",
                "status": "completed",
                "query": "latest news",
                "sources": ["https://example.com"],
            },
        }
    ).root

    assert isinstance(parsed, ToolStatusEvent)
    assert isinstance(parsed.tool, WebSearchTool)
    assert parsed.tool.query == "latest news"


def test_streaming_chat_event_accepts_code_interpreter_tool_status_and_code_done():
    status_event = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_2",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "tool.status",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "researcher",
            "tool": {
                "tool_type": "code_interpreter",
                "tool_call_id": "ci_1",
                "status": "completed",
            },
        }
    ).root
    assert isinstance(status_event, ToolStatusEvent)
    assert isinstance(status_event.tool, CodeInterpreterTool)
    assert status_event.tool.status == "completed"

    code_done = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 2,
            "stream_id": "chat_stream_2",
            "server_timestamp": "2025-12-15T00:00:01Z",
            "kind": "tool.code.done",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "researcher",
            "tool_call_id": "ci_1",
            "code": "print('hi')",
        }
    ).root
    assert isinstance(code_done, ToolCodeDoneEvent)
    assert "print" in code_done.code


def test_streaming_chat_event_accepts_file_search_tool_status_with_results():
    parsed = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_3",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "tool.status",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "researcher",
            "tool": {
                "tool_type": "file_search",
                "tool_call_id": "fs_1",
                "status": "completed",
                "queries": ["what is deep research"],
                "results": [
                    {
                        "file_id": "file_123",
                        "filename": "doc.txt",
                        "vector_store_id": "vs_primary",
                        "score": 0.9,
                    }
                ],
            },
        }
    ).root

    assert isinstance(parsed, ToolStatusEvent)
    assert isinstance(parsed.tool, FileSearchTool)
    assert parsed.tool.status == "completed"


def test_streaming_chat_event_accepts_function_tool_arguments_delta_and_done():
    delta_event = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_4",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "tool.arguments.delta",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "triage",
            "tool_call_id": "call_1",
            "tool_type": "function",
            "tool_name": "get_current_time",
            "delta": "{\"timezone\":\"UTC\"}",
        }
    ).root
    assert isinstance(delta_event, ToolArgumentsDeltaEvent)

    done_event = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 2,
            "stream_id": "chat_stream_4",
            "server_timestamp": "2025-12-15T00:00:01Z",
            "kind": "tool.arguments.done",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "triage",
            "tool_call_id": "call_1",
            "tool_type": "function",
            "tool_name": "get_current_time",
            "arguments_text": "{\"timezone\":\"UTC\"}",
            "arguments_json": {"timezone": "UTC"},
        }
    ).root
    assert isinstance(done_event, ToolArgumentsDoneEvent)
    assert done_event.arguments_json == {"timezone": "UTC"}


def test_streaming_chat_event_accepts_mcp_tool_status():
    parsed = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_5",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "tool.status",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "triage",
            "tool": {
                "tool_type": "mcp",
                "tool_call_id": "mcp_1",
                "status": "awaiting_approval",
                "tool_name": "google_drive.search",
            },
        }
    ).root
    assert isinstance(parsed, ToolStatusEvent)
    assert isinstance(parsed.tool, McpTool)


def test_streaming_chat_event_accepts_reasoning_summary_and_refusal():
    reasoning = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 1,
            "stream_id": "chat_stream_6",
            "server_timestamp": "2025-12-15T00:00:00Z",
            "kind": "reasoning_summary.delta",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "triage",
            "delta": "Summary",
        }
    ).root
    assert isinstance(reasoning, ReasoningSummaryDeltaEvent)

    refusal = StreamingChatEvent.model_validate(
        {
            "schema": "public_sse_v1",
            "event_id": 2,
            "stream_id": "chat_stream_6",
            "server_timestamp": "2025-12-15T00:00:01Z",
            "kind": "refusal.done",
            "conversation_id": "conv_123",
            "response_id": "resp_123",
            "agent": "triage",
            "message_id": "msg_1",
            "refusal_text": "No.",
        }
    ).root
    assert isinstance(refusal, RefusalDoneEvent)
