from __future__ import annotations

import json
import math
from typing import Any, Dict, List

ROLE_USER = "user"


def _extract_usage(
    result: Any,
    messages: List[Dict[str, str]],
    response: str,
    tool_log: List[str],
    tool_events: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Estimate token usage via a cheap character-count heuristic (ceil(chars/4))."""
    _ = result

    def _text_from_content(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, list):
            return "".join(_text_from_content(item) for item in value)
        if isinstance(value, dict):
            parts: List[str] = []
            for key in ("text", "content", "value", "message", "input_text"):
                if key in value:
                    parts.append(_text_from_content(value[key]))
            if not parts:
                for item in value.values():
                    parts.append(_text_from_content(item))
            if parts:
                return "".join(parts)
            try:
                return json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)
        return str(value)

    def _chars_to_tokens(char_count: int) -> int:
        if char_count <= 0:
            return 0
        return int(math.ceil(char_count / 4.0))

    user_char_count = 0
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        if message.get("role") != ROLE_USER:
            continue
        content_text = _text_from_content(message.get("content"))
        user_char_count += len(content_text)

    agent_char_count = len(response or "")

    tool_char_count = 0
    rag_char_count = 0

    if tool_events:
        for event in tool_events:
            if not isinstance(event, dict):
                continue
            output_text = _text_from_content(event.get("output"))
            if not output_text:
                continue
            length = len(output_text)
            tool_char_count += length
            if event.get("name") == "SearchPolicy":
                rag_char_count += length

    if tool_char_count == 0 and tool_log:
        for entry in tool_log:
            if not isinstance(entry, str):
                continue
            arrow_index = entry.find("→")
            raw_output = entry[arrow_index + 1 :].strip() if arrow_index != -1 else entry.strip()
            if not raw_output:
                continue
            decoded_output: Any
            try:
                decoded_output = json.loads(raw_output)
            except (TypeError, ValueError, json.JSONDecodeError):
                decoded_output = raw_output
            output_text = _text_from_content(decoded_output)
            if not output_text:
                continue
            length = len(output_text)
            tool_char_count += length
            if entry.startswith("SearchPolicy"):
                rag_char_count += length

    return {
        "userInput": _chars_to_tokens(user_char_count),
        "agentOutput": _chars_to_tokens(agent_char_count),
        "tools": _chars_to_tokens(tool_char_count),
        "memory": 0,
        "rag": _chars_to_tokens(rag_char_count),
        "basePrompt": 0,
    }


__all__ = ["_extract_usage"]
