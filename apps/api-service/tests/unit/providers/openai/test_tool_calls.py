from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.providers.openai.tool_calls import extract_tool_info


@dataclass
class _RawItem:
    id: str
    type: str
    name: str | None = None


@dataclass
class _Item:
    id: str
    type: str
    raw_item: _RawItem | None = None
    name: str | None = None


def test_extract_tool_info_infers_name_for_web_search_call():
    item = _Item(
        id="ws_item",
        type="tool_call_item",
        raw_item=_RawItem(id="ws_123", type="web_search_call"),
    )

    tool_call_id, tool_name = extract_tool_info(item)
    assert tool_call_id == "ws_123"
    assert tool_name == "web_search"


def test_extract_tool_info_prefers_explicit_name():
    item = _Item(
        id="fn_item",
        type="tool_call_item",
        raw_item=_RawItem(id="call_1", type="function_call", name="my_tool"),
    )

    tool_call_id, tool_name = extract_tool_info(item)
    assert tool_call_id == "call_1"
    assert tool_name == "my_tool"
