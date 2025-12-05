from __future__ import annotations

from types import SimpleNamespace

from app.infrastructure.providers.openai import tool_calls as tc


def test_web_search_status_mapping():
    call = tc.build_web_search_tool_call(item_id="1", status="completed", action={"q": "hi"})
    assert call["web_search_call"]["status"] == "completed"

    call_in_progress = tc.build_web_search_tool_call(item_id="1", status=None)
    assert call_in_progress["web_search_call"]["status"] == "in_progress"


def test_image_generation_alias_b64_json():
    call = tc.build_image_generation_tool_call(
        item_id="img1",
        status="generating",
        result=None,
        partial_image_b64="xyz",
    )
    payload = call["image_generation_call"]
    assert payload["partial_image_b64"] == "xyz"
    assert payload["b64_json"] == "xyz"  # alias maintained for consumers


def test_code_interpreter_normalizes_status_and_container():
    call = tc.build_code_interpreter_tool_call(
        item_id="ci-1",
        status="interpreting",
        container_id="cont-1",
        container_mode="auto",
    )
    payload = call["code_interpreter_call"]
    assert payload["status"] == "interpreting"
    assert payload["container_id"] == "cont-1"
    assert payload["container_mode"] == "auto"


def test_extract_agent_and_tool_info():
    agent_obj = SimpleNamespace(name="alpha")
    nested_agent_obj = SimpleNamespace(agent=SimpleNamespace(name="beta"))
    assert tc.extract_agent_name(agent_obj) == "alpha"
    assert tc.extract_agent_name(nested_agent_obj) == "beta"

    item = SimpleNamespace(id=123, name="search")
    raw_item = SimpleNamespace(id="raw-1", name="raw-search")
    item_with_raw = SimpleNamespace(id=123, name="search", raw_item=raw_item)

    assert tc.extract_tool_info(item) == ("123", "search")
    assert tc.extract_tool_info(item_with_raw) == ("raw-1", "raw-search")


def test_coerce_delta_handles_non_str():
    assert tc.coerce_delta(None) == ""
    assert tc.coerce_delta("hi") == "hi"
    assert tc.coerce_delta(42) == "42"
