from __future__ import annotations

import json
from contextvars import ContextVar
from typing import Any, Dict, List

# --------------------------------------------------------------------------------------
# Tool logging helpers
# --------------------------------------------------------------------------------------

_TOOL_LOG: ContextVar[List[str]] = ContextVar("tool_log", default=[])
_TOOL_EVENTS: ContextVar[List[Dict[str, Any]]] = ContextVar("tool_events", default=[])


def _log_tool_event(entry: str) -> None:
    bucket = _TOOL_LOG.get()
    bucket.append(entry)


def _normalize_tool_output_for_usage(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception:
            return value.decode("utf-8", errors="replace")
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump(exclude_none=True)
        except Exception:
            dumped = None
        if dumped is not None:
            return _normalize_tool_output_for_usage(dumped)
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def _serialize_tool_value(value: Any) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                parsed = json.loads(stripped)
            except (TypeError, ValueError, json.JSONDecodeError):
                return json.dumps(value)
            else:
                try:
                    return json.dumps(parsed)
                except TypeError:
                    return repr(parsed)
        return json.dumps(value)

    if isinstance(value, (int, float, bool)) or value is None:
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return repr(value)

    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return repr(value)

    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump(exclude_none=True)
            return json.dumps(dumped)
        except Exception:
            return repr(value)

    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)


def _log_tool_call(name: str, args: Dict[str, Any], output: Any) -> None:
    normalized_output = _normalize_tool_output_for_usage(output)
    event_bucket = _TOOL_EVENTS.get()
    event_bucket.append({"name": name, "output": normalized_output})

    arg_parts = []
    for key, value in args.items():
        arg_parts.append(f"{key}={_serialize_tool_value(value)}")
    args_repr = ", ".join(arg_parts)
    entry = f"{name}({args_repr}) → {_serialize_tool_value(output)}"
    _log_tool_event(entry)


__all__ = [
    "_TOOL_LOG",
    "_TOOL_EVENTS",
    "_log_tool_event",
    "_log_tool_call",
]
