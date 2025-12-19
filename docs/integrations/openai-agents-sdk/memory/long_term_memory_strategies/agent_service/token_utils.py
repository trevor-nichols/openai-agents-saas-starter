from __future__ import annotations

import json
import math
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .deps import TResponseInputItem

# --------------------------------------------------------------------------------------
# Token estimation helpers for session context accounting
# --------------------------------------------------------------------------------------


def _estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    try:
        return int(math.ceil(len(text) / 4.0))
    except Exception:
        return 0


def _extract_role_and_text(item: TResponseInputItem) -> Tuple[str, str]:
    role = str(getattr(item, "role", "assistant") or "assistant").lower()
    content: Any = getattr(item, "content", "")
    message_type = str(getattr(item, "messageType", "") or "").lower()
    raw_type = ""
    raw: Any = None

    if isinstance(item, dict):
        role = str(item.get("role", role) or role).lower()
        content = item.get("content", content)
        if not message_type:
            message_type = str(item.get("messageType", "") or item.get("type", "") or "").lower()
        raw = item.get("raw")
        if isinstance(raw, dict):
            raw_type = str(raw.get("type", "") or "").lower()
    else:
        raw = getattr(item, "raw", None)
        if isinstance(raw, dict):
            raw_type = str(raw.get("type", "") or "").lower()

    tool_message_types = {"function_call", "function_call_output", "tool", "tool_result"}
    if message_type in tool_message_types or raw_type in tool_message_types:
        role = "tool"

    text_parts: List[str] = []

    def _normalize_text(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, list):
            combined = " ".join(filter(None, (_normalize_text(part) or "" for part in value)))
            return combined or None
        if isinstance(value, dict):
            combined = " ".join(
                filter(
                    None,
                    (
                        _normalize_text(val)
                        for key in ("text", "output", "arguments", "content", "message", "value")
                        for val in ([value.get(key)] if key in value else [])
                    ),
                )
            )
            return combined or None
        return str(value)

    normalized_content = _normalize_text(content)
    if normalized_content:
        text_parts.append(normalized_content)

    # For tool messages, also consider raw payload fields and top-level fallbacks
    extra_sources: List[Any] = []
    if isinstance(item, dict):
        extra_sources.extend(
            [
                item.get("output"),
                item.get("arguments"),
                item.get("data"),
                item.get("text"),
            ]
        )
    if isinstance(raw, dict):
        extra_sources.extend(
            raw.get(key)
            for key in (
                "output",
                "arguments",
                "response",
                "content",
                "summary",
                "details",
                "text",
            )
        )

    for candidate in extra_sources:
        normalized = _normalize_text(candidate)
        if normalized:
            text_parts.append(normalized)

    combined_text = " ".join(text_parts).strip()
    return role, combined_text


def _is_rag_tool_item(item: TResponseInputItem) -> bool:
    """Best-effort detection of retrieval tool items (e.g., SearchPolicy)."""

    def _maybe_add_candidate(value: Any, bucket: List[str]) -> None:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized:
                bucket.append(normalized)

    candidates: List[str] = []

    sources: List[Any] = []
    if isinstance(item, dict):
        sources.append(item)
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            sources.append(metadata)
        tool_call = item.get("tool_call")
        if isinstance(tool_call, dict):
            sources.append(tool_call)
    else:
        sources.append(item)

    for source in sources:
        if isinstance(source, dict):
            for key in ("tool_name", "name", "toolName"):
                _maybe_add_candidate(source.get(key), candidates)
        else:
            for attr in ("tool_name", "name"):
                _maybe_add_candidate(getattr(source, attr, None), candidates)

    return any(candidate == "searchpolicy" for candidate in candidates)


def _estimate_usage_for_items(items: List[TResponseInputItem]) -> Dict[str, int]:
    usage = {"userInput": 0, "agentOutput": 0, "tools": 0, "memory": 0, "rag": 0, "basePrompt": 0}
    for item in items or []:
        role, text = _extract_role_and_text(item)
        tokens = _estimate_tokens_from_text(text)
        if tokens <= 0:
            continue
        is_tool_role = role in {"tool", "tool_result"}
        if role == "user":
            usage["userInput"] += tokens
        elif role == "assistant":
            usage["agentOutput"] += tokens
        elif is_tool_role:
            usage["tools"] += tokens
        else:
            # Count unknown roles toward agent output for safety
            usage["agentOutput"] += tokens
        if is_tool_role and tokens > 0 and _is_rag_tool_item(item):
            usage["rag"] += tokens
    return usage


__all__ = [
    "_estimate_tokens_from_text",
    "_extract_role_and_text",
    "_is_rag_tool_item",
    "_estimate_usage_for_items",
]
