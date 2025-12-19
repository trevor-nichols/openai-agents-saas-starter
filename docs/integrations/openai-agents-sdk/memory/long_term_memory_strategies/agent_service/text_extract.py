from __future__ import annotations

from typing import Any, List, Optional

from openai.types.responses import ResponseOutputMessage, ResponseOutputRefusal, ResponseOutputText

from .deps import MessageOutputItem


def _extract_text_from_message(message: ResponseOutputMessage) -> str:
    parts: List[str] = []
    for content in getattr(message, "content", []) or []:
        candidate: Optional[str] = None

        if isinstance(content, ResponseOutputText):
            candidate = content.text
        elif isinstance(content, ResponseOutputRefusal):
            candidate = content.refusal
        elif isinstance(content, dict):
            candidate = content.get("text") or content.get("refusal")
        else:
            candidate = getattr(content, "text", None) or getattr(content, "refusal", None)
            if candidate is None and hasattr(content, "model_dump"):
                try:
                    data = content.model_dump(exclude_none=True)
                except Exception:  # pragma: no cover - defensive
                    data = None
                if isinstance(data, dict):
                    candidate = data.get("text") or data.get("refusal")

        if isinstance(candidate, str):
            candidate = candidate.strip()
            if candidate:
                parts.append(candidate)

    return "\n".join(parts).strip()


def _extract_text_from_new_items(items: List[Any]) -> str:
    parts: List[str] = []
    for item in items or []:
        if isinstance(item, MessageOutputItem):
            text = _extract_text_from_message(item.raw_item)
            if text:
                parts.append(text)

    return "\n".join(parts).strip()


def _extract_text_from_final_output(final_output: Any) -> str:
    if final_output is None:
        return ""

    if isinstance(final_output, str):
        return final_output.strip()

    if isinstance(final_output, ResponseOutputMessage):
        return _extract_text_from_message(final_output)

    if isinstance(final_output, MessageOutputItem):
        return _extract_text_from_message(final_output.raw_item)

    if isinstance(final_output, dict):
        parts: List[str] = []
        for key in ("content", "text", "refusal", "message", "output"):
            if key in final_output:
                parts.append(_extract_text_from_final_output(final_output[key]))
        if not parts:
            parts.extend(_extract_text_from_final_output(value) for value in final_output.values())
        parts = [part for part in parts if part]
        return "\n".join(parts).strip()

    if isinstance(final_output, (list, tuple)):
        parts = [_extract_text_from_final_output(item) for item in final_output]
        parts = [part for part in parts if part]
        return "\n".join(parts).strip()

    if hasattr(final_output, "model_dump"):
        try:
            dumped = final_output.model_dump(exclude_none=True)
        except Exception:  # pragma: no cover - defensive
            dumped = None
        if dumped is not None:
            return _extract_text_from_final_output(dumped)

    text_attr = getattr(final_output, "text", None)
    if isinstance(text_attr, str):
        return text_attr.strip()

    return ""


__all__ = [
    "_extract_text_from_message",
    "_extract_text_from_new_items",
    "_extract_text_from_final_output",
]
