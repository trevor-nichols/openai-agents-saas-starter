from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from compacting_session import (
    CompactionTrigger,
    CompactingSession,
    _default_token_counter as compacting_default_token_counter,
)

from ..deps import TResponseInputItem

# --------------------------------------------------------------------------------------
# Compacting session wrapper
# --------------------------------------------------------------------------------------


class TrackingCompactingSession(CompactingSession):
    """Extend CompactingSession with delta tracking for the demo UI."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._did_compact_recently: bool = False
        self._last_context_delta_usage: Dict[str, int] = {
            "userInput": 0,
            "agentOutput": 0,
            "tools": 0,
            "memory": 0,
            "rag": 0,
            "basePrompt": 0,
        }
        self._pending_tools_delta: int = 0

    async def add_items(self, items: List[TResponseInputItem]) -> None:  # type: ignore[override]
        if not items:
            return

        await super().add_items(items)

        tools_delta = min(0, self._pending_tools_delta)

        if not isinstance(self._last_context_delta_usage, dict):
            self._last_context_delta_usage = {
                "userInput": 0,
                "agentOutput": 0,
                "tools": 0,
                "memory": 0,
                "rag": 0,
                "basePrompt": 0,
            }

        if tools_delta != 0:
            self._last_context_delta_usage["tools"] = (
                int(self._last_context_delta_usage.get("tools", 0)) + tools_delta
            )

        # Reset pending delta so we only apply each compaction once.
        self._pending_tools_delta = 0

    async def clear_session(self) -> None:  # type: ignore[override]
        await super().clear_session()
        self._did_compact_recently = False
        self._pending_tools_delta = 0
        self._last_context_delta_usage = {
            "userInput": 0,
            "agentOutput": 0,
            "tools": 0,
            "memory": 0,
            "rag": 0,
            "basePrompt": 0,
        }

    def _compact_tool_result(  # type: ignore[override]
        self,
        idx: int,
        *,
        tool_name: Optional[str],
        call_id: Optional[str],
    ) -> None:
        original_item = copy.deepcopy(self._items[idx])
        super()._compact_tool_result(idx, tool_name=tool_name, call_id=call_id)
        self._record_compaction_delta(original_item, self._items[idx])

    def _compact_tool_call(  # type: ignore[override]
        self,
        idx: int,
        *,
        tool_name: Optional[str],
        call_id: Optional[str],
    ) -> None:
        original_item = copy.deepcopy(self._items[idx])
        super()._compact_tool_call(idx, tool_name=tool_name, call_id=call_id)
        self._record_compaction_delta(original_item, self._items[idx])

    def _token_count(self, item: TResponseInputItem) -> int:
        if (
            item.get("compacted")
            or item.get("messageType") in {"compacted_tool_result", "compacted_tool_call"}
            or item.get("type") in {"compacted_tool_result", "compacted_tool_call"}
        ):
            return 0
        counter = self.token_counter or compacting_default_token_counter
        return max(0, counter(item))

    def _record_compaction_delta(
        self,
        before: TResponseInputItem,
        after: TResponseInputItem,
    ) -> None:
        before_tokens = self._token_count(before)
        after_tokens = self._token_count(after)
        delta = after_tokens - before_tokens
        if delta < 0:
            self._pending_tools_delta += delta
        self._did_compact_recently = True


__all__ = ["TrackingCompactingSession", "CompactionTrigger", "CompactingSession"]
