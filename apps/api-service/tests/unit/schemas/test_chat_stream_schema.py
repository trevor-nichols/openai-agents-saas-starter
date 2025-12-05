from app.api.v1.chat.schemas import (
    StreamingChatEvent,
    ToolCallPayload,
    WebSearchCall,
    WebSearchAction,
    UrlCitation,
    CodeInterpreterCall,
    FileSearchCall,
)


def test_streaming_chat_event_accepts_tool_call_and_citation():
    event = StreamingChatEvent(
        kind="raw_response_event",
        conversation_id="conv_123",
        is_terminal=False,
        raw_event={"kind": "raw_response_event", "raw_type": "response.output_text.delta"},
        text_delta="Hello",
        tool_call=ToolCallPayload(
            tool_type="web_search",
            web_search_call=WebSearchCall(
                id="ws_1",
                type="web_search_call",
                status="completed",
                action=WebSearchAction(
                    type="search",
                    query="latest news",
                    sources=["https://example.com"],
                ),
            ),
        ),
        annotations=[
            UrlCitation(
                start_index=0,
                end_index=5,
                url="https://example.com",
                title="Example",
            )
        ],
    )

    assert event.tool_call is not None
    assert event.tool_call.web_search_call is not None
    assert event.tool_call.web_search_call.action is not None
    assert event.tool_call.web_search_call.action.query == "latest news"
    assert event.annotations is not None
    assert event.annotations[0].url == "https://example.com"


def test_streaming_chat_event_accepts_code_interpreter_tool_call():
    event = StreamingChatEvent(
        kind="raw_response_event",
        conversation_id="conv_123",
        is_terminal=False,
        raw_event={"type": "response.code_interpreter_call.completed"},
        tool_call=ToolCallPayload(
            tool_type="code_interpreter",
            code_interpreter_call=CodeInterpreterCall(
                id="ci_1",
                type="code_interpreter_call",
                status="completed",
                code="print('hi')",
                outputs=[{"text": "hi"}],
            ),
        ),
    )

    assert event.tool_call is not None
    assert event.tool_call.code_interpreter_call is not None
    assert event.tool_call.code_interpreter_call.status == "completed"


def test_streaming_chat_event_accepts_file_search_tool_call():
    event = StreamingChatEvent(
        kind="raw_response_event",
        conversation_id="conv_123",
        is_terminal=False,
        raw_event={"type": "response.file_search_call.completed"},
        tool_call=ToolCallPayload(
            tool_type="file_search",
            file_search_call=FileSearchCall(
                id="fs_1",
                type="file_search_call",
                status="completed",
                queries=["what is deep research"],
                results=[{"id": "doc1"}],
            ),
        ),
    )

    assert event.tool_call is not None
    assert event.tool_call.file_search_call is not None
    assert event.tool_call.file_search_call.status == "completed"
