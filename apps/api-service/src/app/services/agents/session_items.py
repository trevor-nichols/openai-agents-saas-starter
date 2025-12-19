"""Provider-neutral session item helpers.

The Agents SDK session store is an implementation detail of a provider, but our
service layer needs two stable behaviors:

- Best-effort retrieval of the current session items for event projection.
- A delta algorithm that still works when the session rewrites history
  (e.g., memory strategies that clear + re-add items).
"""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

logger = logging.getLogger(__name__)


async def get_session_items(session_handle: Any) -> list[dict[str, Any]]:
    """Safely read items from a provider session handle."""

    getter = getattr(session_handle, "get_items", None)
    if getter is None or not callable(getter):
        return []
    try:
        result = getter()
        items = await result if inspect.isawaitable(result) else result
        if items is None or not isinstance(items, Iterable):
            return []
        return list(items)
    except Exception:  # pragma: no cover - defensive
        logger.exception("session_items_fetch_failed")
        return []


def compute_session_delta(
    pre_items: Iterable[Mapping[str, Any]], post_items: Iterable[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """Return post items that are new or rewritten vs pre.

    Strategy sessions may rewrite history (clear + re-add). We diff by fingerprint
    instead of assuming monotonic growth so trimmed/summarized/compacted runs
    still emit newly produced items.
    """

    pre_counts = Counter(_fingerprint(it) for it in pre_items)
    delta: list[Mapping[str, Any]] = []
    for item in post_items:
        fp = _fingerprint(item)
        if pre_counts.get(fp, 0) > 0:
            pre_counts[fp] -= 1
            continue
        delta.append(item)
    return delta


def _fingerprint(item: Mapping[str, Any]) -> str:
    key = _stable_item_key(item)
    try:
        normalized = json.dumps(item, sort_keys=True, default=str)
    except TypeError:
        normalized = repr(item)
    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    return f"{key}:{digest}"


def _stable_item_key(item: Mapping[str, Any]) -> str:
    for candidate in (
        "id",
        "tool_call_id",
        "call_id",
        "response_id",
        "timestamp",
    ):
        value = item.get(candidate)
        if value:
            return str(value)
    role = item.get("role") or "unknown"
    item_type = item.get("type") or "unknown"
    return f"{item_type}:{role}"


__all__ = ["compute_session_delta", "get_session_items"]

