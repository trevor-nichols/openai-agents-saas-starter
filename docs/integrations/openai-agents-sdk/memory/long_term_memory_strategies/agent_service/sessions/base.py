from __future__ import annotations

import asyncio
import copy
import sys
from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

from openai import AsyncOpenAI

from ..deps import SessionABC, TResponseInputItem
from ..openai_client import ensure_openai_client
from ..stores import _persist_summary_to_disk
from ..token_utils import _estimate_usage_for_items

# --------------------------------------------------------------------------------------
# Session management helpers (trimmed + summarizing)
# --------------------------------------------------------------------------------------

ROLE_USER = "user"


def _is_user_msg(item: TResponseInputItem) -> bool:
    if isinstance(item, dict):
        role = item.get("role")
        if role is not None:
            return role == ROLE_USER
        if item.get("type") == "message":
            return item.get("role") == ROLE_USER
    return getattr(item, "role", None) == ROLE_USER


def _count_user_turns(items: Iterable[TResponseInputItem]) -> int:
    if not items:
        return 0
    return sum(1 for item in items if _is_user_msg(item))


class _InternalTurnCounterMixin:
    """Shared helper to track per-session turns independent of global counts."""

    def __init__(self) -> None:
        self._internal_turn_counter: int = 0

    @property
    def internalTurnCounter(self) -> int:  # noqa: N802 - camelCase required for UI contract
        return self._internal_turn_counter

    @internalTurnCounter.setter
    def internalTurnCounter(self, value: int) -> None:  # noqa: N802 - camelCase setter
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            numeric = 0
        self._internal_turn_counter = max(0, numeric)

    def _increment_internal_turn_counter(self, items: Iterable[TResponseInputItem]) -> None:
        if not items:
            return
        self._internal_turn_counter += _count_user_turns(items)

    def _reset_internal_turn_counter(self) -> None:
        self._internal_turn_counter = 0


SUMMARY_PROMPT = """
You are a senior customer-support assistant for tech devices, setup, and software issues.
Compress the earlier conversation into a precise, reusable snapshot for future turns.

Before you write (do this silently):
- Contradiction check: compare user claims with system instructions and tool definitions/logs; note any conflicts or reversals.
- Temporal ordering: sort key events by time; the most recent update wins. If timestamps exist, keep them.
- Hallucination control: if any fact is uncertain/not stated, mark it as UNVERIFIED rather than guessing.

Write a structured, factual summary ≤ 200 words using the sections below (use the exact headings):

• Product & Environment:
  - Device/model, OS/app versions, network/context if mentioned.

• Reported Issue:
  - Single-sentence problem statement (latest state).

• Steps Tried & Results:
  - Chronological bullets (include tool calls + outcomes, errors, codes).

• Identifiers:
  - Ticket #, device serial/model, account/email (only if provided).

• Timeline Milestones:
  - Key events with timestamps or relative order (e.g., 10:32 install → 10:41 error).

• Tool Performance Insights:
  - What tool calls worked/failed and why (if evident).

• Current Status & Blockers:
  - What’s resolved vs pending; explicit blockers preventing progress.

• Next Recommended Step:
  - One concrete action (or two alternatives) aligned with policies/tools.

Rules:
- Be concise, no fluff; use short bullets, verbs first.
- Do not invent new facts; quote error strings/codes exactly when available.
- If previous info was superseded, note “Superseded:” and omit details unless critical.
"""


class LLMSummarizer:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "gpt-4o",
        max_tokens: int = 400,
        tool_trim_limit: int = 600,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.tool_trim_limit = tool_trim_limit

    async def summarize(self, messages: List[TResponseInputItem]) -> Tuple[str, str]:
        """Return a shadow user line and structured summary for the provided messages."""
        user_shadow = "Summarize the conversation we had so far."
        tool_roles = {"tool", "tool_result"}

        def _extract_content(item: TResponseInputItem) -> Tuple[str, str, Dict[str, Any]]:
            role = "assistant"
            content = ""
            metadata: Dict[str, Any] = {}
            if isinstance(item, dict):
                role = str(item.get("role") or "assistant")
                raw_content = item.get("content")
                meta_candidate = item.get("metadata")
                if isinstance(meta_candidate, dict):
                    metadata = meta_candidate
            else:
                role = str(getattr(item, "role", "assistant"))
                raw_content = getattr(item, "content", "")

            if isinstance(raw_content, list):
                content = " ".join(str(part) for part in raw_content if part)
            else:
                content = str(raw_content or "")

            role = role.lower()
            if role in tool_roles and len(content) > self.tool_trim_limit:
                content = content[: self.tool_trim_limit] + " …"
            return role.upper(), content.strip(), metadata

        snippets: List[str] = []
        for item in messages:
            role, content, metadata = _extract_content(item)
            if metadata.get("summary"):
                continue
            if content:
                snippets.append(f"{role}: {content}")

        if not snippets:
            return user_shadow, ""

        system_content = SUMMARY_PROMPT.strip()
        user_content = "\n".join(snippets)
        prompt_messages: List[Dict[str, Any]] = []
        if system_content:
            prompt_messages.append(
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_content,
                        }
                    ],
                }
            )
        if user_content:
            prompt_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_content,
                        }
                    ],
                }
            )

        summary_text = ""
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=prompt_messages,
                max_output_tokens=self.max_tokens,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            print(
                f"[agents-python] Warning: summarization call failed ({exc}); falling back to placeholder.",
                file=sys.stderr,
            )
            return user_shadow, "Summary of earlier conversation (unavailable)."

        summary_text = getattr(response, "output_text", None) or ""

        if not summary_text:
            output = getattr(response, "output", None) or []
            parts: List[str] = []
            for item in output:
                content_list = getattr(item, "content", []) or []
                for content in content_list:
                    text_block = getattr(content, "text", None)
                    if text_block and hasattr(text_block, "value"):
                        parts.append(str(text_block.value))
                    elif hasattr(content, "text"):
                        parts.append(str(getattr(content, "text")))
            summary_text = "\n".join(part for part in parts if part)

        return user_shadow, summary_text.strip()


class DefaultSession(_InternalTurnCounterMixin, SessionABC):
    """Maintain the full conversation history without trimming."""

    def __init__(self, session_id: str):
        _InternalTurnCounterMixin.__init__(self)
        self.session_id = session_id
        self._items: Deque[TResponseInputItem] = deque()
        self._lock = asyncio.Lock()
        # Tracks the net token delta applied to the session context due to
        # trimming/summarization during the latest add_items operation.
        # Negative numbers indicate removal from the active context.
        self._last_context_delta_usage: Dict[str, int] = {
            "userInput": 0,
            "agentOutput": 0,
            "tools": 0,
            "memory": 0,
            "rag": 0,
            "basePrompt": 0,
        }

    async def get_items(self, limit: Optional[int] = None) -> List[TResponseInputItem]:
        async with self._lock:
            snapshot = list(self._items)
        return snapshot[-limit:] if (limit is not None and limit >= 0) else snapshot

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        if not items:
            return
        async with self._lock:
            self._increment_internal_turn_counter(items)
            self._items.extend(items)

    async def pop_item(self) -> Optional[TResponseInputItem]:
        async with self._lock:
            if not self._items:
                return None
            return self._items.pop()

    async def clear_session(self) -> None:
        async with self._lock:
            self._items.clear()
            # Reset any pending context delta since the session is emptied
            self._last_context_delta_usage = {
                "userInput": 0,
                "agentOutput": 0,
                "tools": 0,
                "memory": 0,
                "rag": 0,
                "basePrompt": 0,
            }
            self._reset_internal_turn_counter()

    async def set_max_turns(self, _: int) -> None:
        # Default sessions do not enforce a turn limit.
        return None


class TrimmingSession(_InternalTurnCounterMixin, SessionABC):
    """Keep only the last N user turns, with optional hysteresis.

    - max_turns: threshold at which trimming triggers
    - keep_last_n_turns: after trimming triggers, keep only this many most recent turns

    Example: max_turns=6, keep_last_n_turns=4
      When the session reaches 6 total turns, drop the earliest 2 turns (keep last 4).
    """

    def __init__(self, session_id: str, max_turns: int = 8, keep_last_n_turns: Optional[int] = None):
        _InternalTurnCounterMixin.__init__(self)
        self.session_id = session_id
        self.max_turns = max(1, int(max_turns))

        # Default preserves prior behavior: always keep last `max_turns` turns.
        if keep_last_n_turns is None:
            keep_last_n_turns = self.max_turns
        self.keep_last_n_turns = max(1, int(keep_last_n_turns))
        # Ensure keep_last_n_turns never exceeds max_turns (otherwise trimming threshold is meaningless)
        self.keep_last_n_turns = min(self.keep_last_n_turns, self.max_turns)

        self._items: Deque[TResponseInputItem] = deque()
        self._lock = asyncio.Lock()
        self._did_trim_recently: bool = False
        self._last_total_turns: int = 0
        self._last_context_delta_usage: Dict[str, int] = {
            "userInput": 0,
            "agentOutput": 0,
            "tools": 0,
            "memory": 0,
            "rag": 0,
            "basePrompt": 0,
        }

    async def get_items(self, limit: Optional[int] = None) -> List[TResponseInputItem]:
        async with self._lock:
            trimmed, _ = self._trim_to_last_turns(list(self._items))
        return trimmed[-limit:] if (limit is not None and limit >= 0) else trimmed

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        if not items:
            return
        async with self._lock:
            pending: List[TResponseInputItem] = list(self._items)
            self._increment_internal_turn_counter(items)
            pending.extend(items)
            should_trim = self.internalTurnCounter >= self.max_turns
            trimmed, total_turns = self._trim_to_last_turns(pending, force_trim=should_trim)
            self._last_total_turns = total_turns

            if len(trimmed) < len(pending):
                self._did_trim_recently = True
                removed_count = len(pending) - len(trimmed)
                removed_items = pending[:removed_count]
                delta = _estimate_usage_for_items(removed_items)

                if not isinstance(self._last_context_delta_usage, dict):
                    self._last_context_delta_usage = {
                        "userInput": 0,
                        "agentOutput": 0,
                        "tools": 0,
                        "memory": 0,
                        "rag": 0,
                        "basePrompt": 0,
                    }

                current_delta = dict(self._last_context_delta_usage)
                current_delta["userInput"] = int(current_delta.get("userInput", 0)) - delta["userInput"]
                current_delta["agentOutput"] = int(current_delta.get("agentOutput", 0)) - delta["agentOutput"]
                current_delta["tools"] = int(current_delta.get("tools", 0)) - delta["tools"]
                current_delta["rag"] = int(current_delta.get("rag", 0)) - delta["rag"]
                current_delta.setdefault("memory", 0)
                current_delta.setdefault("basePrompt", 0)
                self._last_context_delta_usage = current_delta
                self.internalTurnCounter = min(self.keep_last_n_turns, _count_user_turns(trimmed))
            else:
                self._did_trim_recently = False

            self._items.clear()
            self._items.extend(trimmed)

    async def pop_item(self) -> Optional[TResponseInputItem]:
        async with self._lock:
            if not self._items:
                return None
            return self._items.pop()

    async def clear_session(self) -> None:
        async with self._lock:
            self._items.clear()
            self._last_total_turns = 0
            self._did_trim_recently = False
            self._last_context_delta_usage = {
                "userInput": 0,
                "agentOutput": 0,
                "tools": 0,
                "memory": 0,
                "rag": 0,
                "basePrompt": 0,
            }
            self._reset_internal_turn_counter()

    async def set_max_turns(self, max_turns: int) -> None:
        async with self._lock:
            new_max = max(1, int(max_turns))
            if new_max == self.max_turns:
                self.keep_last_n_turns = min(self.keep_last_n_turns, self.max_turns)
                self.internalTurnCounter = min(self.internalTurnCounter, self.max_turns)
                return

            self.max_turns = new_max
            self.keep_last_n_turns = min(self.keep_last_n_turns, self.max_turns)

            current_items: List[TResponseInputItem] = list(self._items)
            trimmed, total_turns = self._trim_to_last_turns(current_items)
            self._last_total_turns = total_turns
            if len(trimmed) < len(current_items):
                self._did_trim_recently = True
                self.internalTurnCounter = min(self.keep_last_n_turns, _count_user_turns(trimmed))
            else:
                self._did_trim_recently = False
                self.internalTurnCounter = min(self.internalTurnCounter, self.max_turns)
            self._items.clear()
            self._items.extend(trimmed)

    async def set_keep_last_n_turns(self, keep_last_n_turns: int) -> None:
        async with self._lock:
            new_keep = max(1, int(keep_last_n_turns))
            new_keep = min(new_keep, self.max_turns)

            if new_keep == self.keep_last_n_turns:
                self.internalTurnCounter = min(self.internalTurnCounter, self.max_turns)
                return

            self.keep_last_n_turns = new_keep

            current_items: List[TResponseInputItem] = list(self._items)
            current_total_turns = _count_user_turns(current_items)
            force_trim = current_total_turns > self.keep_last_n_turns
            trimmed, total_turns = self._trim_to_last_turns(current_items, force_trim=force_trim)
            self._last_total_turns = total_turns
            if len(trimmed) < len(current_items):
                self._did_trim_recently = True
                self.internalTurnCounter = min(self.keep_last_n_turns, _count_user_turns(trimmed))
            else:
                self._did_trim_recently = False
                self.internalTurnCounter = min(self.internalTurnCounter, self.max_turns)
            self._items.clear()
            self._items.extend(trimmed)

    def _trim_to_last_turns(
        self, items: List[TResponseInputItem], *, force_trim: bool = False
    ) -> Tuple[List[TResponseInputItem], int]:
        if not items:
            return items, 0

        # Count total "turns" = number of user messages in the item stream.
        total_turns = 0
        for it in items:
            if _is_user_msg(it):
                total_turns += 1

        # Hysteresis behavior:
        # - If we haven't reached max_turns yet, do nothing.
        # - Once we reach/exceed max_turns, trim down to keep_last_n_turns.
        if not force_trim and total_turns < self.max_turns:
            return items, total_turns

        # Find the start index of the last `keep_last_n_turns` turns.
        keep = self.keep_last_n_turns
        count = 0
        start_idx = 0
        for i in range(len(items) - 1, -1, -1):
            if _is_user_msg(items[i]):
                count += 1
                if count == keep:
                    start_idx = i
                    break

        trimmed = items[start_idx:] if count >= keep else items
        return trimmed, total_turns


class SummarizingSession(TrimmingSession):
    """Simplified summarizing session: keeps last N turns & adds a synthetic summary."""

    def __init__(
        self,
        session_id: str,
        keep_last_n_turns: int = 3,
        context_limit: int = 7,
        summarizer: Optional[LLMSummarizer] = None,
    ):
        super().__init__(session_id, max_turns=context_limit)
        self.keep_last_n_turns = max(0, int(keep_last_n_turns))
        self._summarizer = summarizer or LLMSummarizer(ensure_openai_client())
        self._last_summary: Optional[Dict[str, str]] = None
        # Tracks whether summarization occurred during the latest update cycle
        self._did_summarize_recently: bool = False

    def configure_limits(self, keep_last_n_turns: int, context_limit: int) -> None:
        self.keep_last_n_turns = max(0, int(keep_last_n_turns))
        self.max_turns = max(1, int(context_limit))

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        if not items:
            return

        # Combine existing items with new ones BEFORE any trimming, so we can detect
        # when we've exceeded the max user turns and produce a summary of the prefix.
        async with self._lock:
            combined: List[TResponseInputItem] = list(self._items)
            self._increment_internal_turn_counter(items)
            current_turn_counter = self._internal_turn_counter
            combined.extend(items)

        should_summarize = current_turn_counter >= self.max_turns
        if not should_summarize:
            # Haven't reached the limit yet; keep at most the last N user turns like trimming.
            trimmed, _ = self._trim_to_last_turns(combined)
            trimmed_count_changed = len(trimmed) < len(combined)
            async with self._lock:
                self._items.clear()
                self._items.extend(trimmed)
                if trimmed_count_changed:
                    trimmed_user_turns = _count_user_turns(trimmed)
                    self._internal_turn_counter = max(0, min(trimmed_user_turns, self.max_turns))
            return

        user_indices = [idx for idx, item in enumerate(combined) if _is_user_msg(item)]
        # We exceeded the context limit: summarize the earlier prefix and keep only the last K user turns.
        if self.keep_last_n_turns <= 0 or self.keep_last_n_turns >= len(user_indices):
            boundary_idx = 0 if self.keep_last_n_turns >= len(user_indices) else len(combined)
        else:
            boundary_idx = user_indices[-self.keep_last_n_turns]
        boundary_idx = max(0, min(boundary_idx, len(combined)))
        prefix = combined[:boundary_idx]
        suffix = combined[boundary_idx:]

        shadow_line = ""
        summary_text = ""
        summary_triggered = bool(prefix)
        if prefix:
            try:
                shadow_line, summary_text = await self._summarizer.summarize(prefix)
                # Mark that a summarization has been performed for this session
                self._did_summarize_recently = True
            except Exception as exc:  # pragma: no cover - defensive logging
                print(
                    f"[agents-python] Warning: summarization failed ({exc}); using fallback text.",
                    file=sys.stderr,
                )
                shadow_line = "Summarize the conversation we had so far."
                summary_text = "Summary of earlier conversation (temporary fallback)."
                self._did_summarize_recently = True

        synthetic_items: List[TResponseInputItem] = []
        summary_payload: Optional[Dict[str, str]] = None
        if prefix and summary_text:
            summary_payload = {
                "shadow_line": shadow_line,
                "summary_text": summary_text,
            }
            if shadow_line:
                synthetic_items.append(
                    {
                        "role": "user",
                        "content": shadow_line,
                    }
                )
            synthetic_items.append(
                {
                    "role": "assistant",
                    "content": summary_text,
                }
            )

        fallback_trimmed: List[TResponseInputItem] = []
        fallback_trimmed_changed = False
        if not synthetic_items:
            fallback_trimmed, _ = self._trim_to_last_turns(combined)
            fallback_trimmed_changed = len(fallback_trimmed) < len(combined)

        removed_items_for_delta: List[TResponseInputItem] = []
        if prefix:
            removed_items_for_delta = list(prefix)
        elif fallback_trimmed_changed:
            removed_count = len(combined) - len(fallback_trimmed)
            removed_items_for_delta = combined[:removed_count]

        async with self._lock:
            self._last_summary = summary_payload
            self._items.clear()
            if synthetic_items:
                self._items.extend(synthetic_items)
                self._items.extend(suffix)
            else:
                # Fallback: if for some reason we could not create a summary, at least trim.
                self._items.extend(fallback_trimmed)

            # Compute and store context delta usage due to summarization.
            # Items removed via summarization/trimming are reported as negative deltas
            # so the UI can apply them immediately (same turn as any added memory tokens).
            if removed_items_for_delta:
                removed_usage = _estimate_usage_for_items(removed_items_for_delta)
                self._last_context_delta_usage = {
                    "userInput": -removed_usage["userInput"],
                    "agentOutput": -removed_usage["agentOutput"],
                    "tools": -removed_usage["tools"],
                    # memory will be added at run time based on summary_text length
                    "memory": 0,
                    "rag": -removed_usage["rag"],
                    "basePrompt": 0,
                }
            else:
                self._last_context_delta_usage = {
                    "userInput": 0,
                    "agentOutput": 0,
                    "tools": 0,
                    "memory": 0,
                    "rag": 0,
                    "basePrompt": 0,
                }
            if summary_triggered:
                retained_turns = _count_user_turns(suffix)
                synthetic_turn = 1 if synthetic_items else 0
                adjusted_turns = retained_turns + synthetic_turn
                self._internal_turn_counter = max(0, min(adjusted_turns, self.max_turns))
            elif fallback_trimmed_changed:
                fallback_turns = _count_user_turns(fallback_trimmed)
                self._internal_turn_counter = max(0, min(fallback_turns, self.max_turns))

        if summary_payload:
            await asyncio.to_thread(
                _persist_summary_to_disk,
                summary_payload.get("shadow_line", ""),
                summary_payload.get("summary_text", ""),
            )

    async def clear_session(self) -> None:
        await super().clear_session()
        async with self._lock:
            self._last_summary = None

    async def get_last_summary(self) -> Optional[Dict[str, str]]:
        async with self._lock:
            if not self._last_summary:
                return None
            return dict(self._last_summary)


__all__ = [
    "ROLE_USER",
    "LLMSummarizer",
    "DefaultSession",
    "TrimmingSession",
    "SummarizingSession",
    "_is_user_msg",
    "_count_user_turns",
    "_InternalTurnCounterMixin",
]
