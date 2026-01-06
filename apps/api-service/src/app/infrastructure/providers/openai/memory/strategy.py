"""Strategy-aware session wrappers atop SQLAlchemySession.

The goal is to keep mutations scoped to the SDK session view while leaving our
durable audit history untouched. Strategies are turn-based for now; token-based
triggers can be layered later without changing callers.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast, overload

from agents.memory.session import SessionABC

from app.observability.metrics import MEMORY_TOKENS_BEFORE_AFTER, MEMORY_TRIGGER_TOTAL


class MemoryStrategy(str, Enum):
    NONE = "none"
    TRIM = "trim"
    SUMMARIZE = "summarize"
    COMPACT = "compact"


@dataclass(slots=True)
class MemoryStrategyConfig:
    mode: MemoryStrategy = MemoryStrategy.NONE
    # Shared knobs
    max_user_turns: int | None = None  # trim/summarize trigger (user turns)
    keep_last_user_turns: int = 0
    # Token/window knobs
    context_window_tokens: int = 400_000
    token_remaining_pct: float | None = None  # triggers when remaining <= pct
    token_soft_remaining_pct: float | None = None
    # Optional token budgets (logical tokens, not billed tokens)
    token_budget: int | None = None
    token_soft_budget: int | None = None
    # Compacting specifics
    compact_trigger_turns: int | None = None
    compact_keep: int = 2
    compact_clear_tool_inputs: bool = False
    compact_exclude_tools: frozenset[str] = frozenset()
    compact_include_tools: frozenset[str] = frozenset()
    # Summarization specifics
    summarizer: Summarizer | None = None
    summary_prefix: str = "[summary]"
    summarizer_model: str | None = None
    summary_max_tokens: int = 300
    summary_max_chars: int = 4000


logger = logging.getLogger(__name__)


class Summarizer:
    """Lightweight interface so callers can plug real LLM summarizers later."""

    async def summarize(self, text: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class NoopSummarizer(Summarizer):
    async def summarize(self, text: str) -> str:  # pragma: no cover - trivial
        return text


class StrategySession(SessionABC):
    """Delegates storage to an underlying SessionABC and applies a strategy.

    The wrapper is intentionally minimal: it fetches the current items,
    applies the strategy in-memory, clears the underlying store, then writes
    the transformed list back. This keeps the logic deterministic and easy to
    reason about while avoiding provider-specific side effects.
    """

    def __init__(
        self,
        base: SessionABC,
        config: MemoryStrategyConfig,
        *,
        on_summary: Callable[[str], Awaitable[None]] | None = None,
        on_compaction: Callable[[Mapping[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self._base = base
        self._config = config
        self._summarizer: Summarizer = config.summarizer or NoopSummarizer()
        self._on_summary = on_summary
        self._on_compaction = on_compaction

    # SessionABC API -------------------------------------------------
    async def get_items(self, limit: int | None = None):
        return await self._base.get_items(limit=limit)

    async def add_items(self, items: list[dict[str, Any]]) -> None:  # type: ignore[override]
        # Pull existing, apply strategy to combined list, then replace
        existing = await self._base.get_items()
        combined: list[dict[str, Any]] = [dict(it) for it in existing] + [dict(it) for it in items]
        updated = await self._apply_strategy(combined)
        await self._base.clear_session()
        await self._base.add_items(cast(list[dict[str, Any]], updated))  # type: ignore[arg-type]

    async def pop_item(self):
        return await self._base.pop_item()

    async def clear_session(self) -> None:
        await self._base.clear_session()

    # Strategy driver -----------------------------------------------
    async def _apply_strategy(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mode = self._config.mode
        total_tokens_est = _estimate_total_tokens(items)
        token_budget = self._config.token_budget
        token_soft_budget = self._config.token_soft_budget
        triggered_by_tokens = token_budget is not None and total_tokens_est >= token_budget
        triggered_by_tokens_soft = (
            token_soft_budget is not None and total_tokens_est >= token_soft_budget
        )
        force_by_tokens = triggered_by_tokens or triggered_by_tokens_soft
        trigger_reason = None
        if triggered_by_tokens:
            trigger_reason = "token_budget"
        elif triggered_by_tokens_soft:
            trigger_reason = "token_soft_budget"
        if mode == MemoryStrategy.NONE:
            return items
        if mode == MemoryStrategy.TRIM:
            trimmed = _trim_items(
                items,
                max_turns=self._config.max_user_turns,
                keep_last=self._config.keep_last_user_turns,
                force=force_by_tokens,
            )
            if trimmed is not items:
                _record_trigger(mode, trigger_reason or "turns")
                _record_tokens(mode, trigger_reason or "turns", total_tokens_est, trimmed)
            return trimmed
        if mode == MemoryStrategy.SUMMARIZE:
            summarized = await _summarize_items(
                items,
                max_turns=self._config.max_user_turns,
                keep_last=self._config.keep_last_user_turns,
                summarizer=self._summarizer,
                summary_prefix=self._config.summary_prefix,
                on_summary=self._on_summary,
                force=force_by_tokens,
            )
            if summarized is not items:
                _record_trigger(mode, trigger_reason or "turns")
                _record_tokens(mode, trigger_reason or "turns", total_tokens_est, summarized)
            return summarized
        if mode == MemoryStrategy.COMPACT:
            compacted, details = _compact_items(
                items,
                trigger_turns=self._config.compact_trigger_turns,
                keep=self._config.compact_keep,
                clear_tool_inputs=self._config.compact_clear_tool_inputs,
                exclude_tools=self._config.compact_exclude_tools,
                include_tools=self._config.compact_include_tools,
                force=force_by_tokens,
                return_details=True,
            )
            if details is None or compacted is items:
                return compacted

            details = dict(details)
            details.setdefault("strategy", "compact")
            details.update(
                {
                    "token_budget": token_budget,
                    "token_soft_budget": token_soft_budget,
                    "tokens_before": total_tokens_est,
                    "tokens_after": _estimate_total_tokens(compacted),
                    "trigger_reason": (
                        "token_budget"
                        if triggered_by_tokens
                        else "token_soft_budget"
                        if triggered_by_tokens_soft
                        else "turns"
                    ),
                }
            )
            _record_trigger(mode, details.get("trigger_reason", "turns"))
            if self._on_compaction:
                await self._on_compaction(details)
            try:
                logger.info(
                    "memory.compaction_applied",
                    extra={
                        "strategy": "compact",
                        "trigger_reason": details.get("trigger_reason"),
                        "tokens_before": details.get("tokens_before"),
                        "tokens_after": details.get("tokens_after"),
                        "compacted_inputs": details.get("compacted_inputs"),
                        "compacted_outputs": details.get("compacted_outputs"),
                    },
                )
            except Exception:
                pass
            _record_tokens(
                mode,
                details.get("trigger_reason", "turns"),
                details.get("tokens_before", total_tokens_est),
                compacted,
            )
            return compacted
        return items


# Utilities ---------------------------------------------------------------


def _is_user(item: Mapping[str, Any]) -> bool:
    role = (item.get("role") or "").lower()
    if role == "user":
        return True
    message_type = (item.get("messageType") or item.get("type") or "").lower()
    return message_type == "user"


def _group_by_turns(items: Sequence[Mapping[str, Any]]) -> list[list[int]]:
    """Return list of index lists, one per user-anchored turn."""

    turns: list[list[int]] = []
    current: list[int] = []
    for idx, item in enumerate(items):
        if _is_user(item):
            if current:
                turns.append(current)
            current = [idx]
        else:
            current.append(idx)
    if current:
        turns.append(current)
    return turns


def _trim_items(
    items: list[dict[str, Any]],
    *,
    max_turns: int | None,
    keep_last: int,
    force: bool = False,
) -> list[dict[str, Any]]:
    if (max_turns is None or max_turns <= 0) and not force:
        return items

    turns = _group_by_turns(items)
    if len(turns) <= (max_turns or 0) and not force:
        return items

    keep_tail = turns[-max(1, keep_last) :] if keep_last > 0 else []
    if keep_tail:
        trimmed_turns = keep_tail
    else:
        limit = max_turns if max_turns and max_turns > 0 else len(turns)
        trimmed_turns = turns[-limit:]
    indices = [i for t in trimmed_turns for i in t]
    return [items[i] for i in sorted(indices)]


async def _summarize_items(
    items: list[dict[str, Any]],
    *,
    max_turns: int | None,
    keep_last: int,
    summarizer: Summarizer,
    summary_prefix: str,
    on_summary: Callable[[str], Awaitable[None]] | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    if (max_turns is None or max_turns <= 0) and not force:
        return items

    turns = _group_by_turns(items)
    if len(turns) <= (max_turns or 0) and not force:
        return items

    tail_turns = turns[-max(1, keep_last) :] if keep_last > 0 else turns[-1:]
    tail_indices = [i for t in tail_turns for i in t]
    prefix_indices = [i for t in turns[:-len(tail_turns)] for i in t]
    prefix_text = _collect_text([items[i] for i in prefix_indices])
    summary = await summarizer.summarize(prefix_text)
    if on_summary is not None:
        try:
            await on_summary(summary)
        except Exception:  # pragma: no cover - best effort
            pass

    summary_items = [
        {
            "role": "user",
            "content": f"{summary_prefix} prior context",
            "type": "message",
        },
        {
            "role": "assistant",
            "content": summary,
            "type": "message",
        },
    ]

    tail_items = [items[i] for i in sorted(tail_indices)]
    return summary_items + tail_items


def _collect_text(items: Iterable[Mapping[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        content = item.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, Mapping):
                    text = c.get("text")
                    if isinstance(text, str):
                        parts.append(text)
    return "\n".join(parts)


def _is_tool_call(item: Mapping[str, Any]) -> bool:
    t = (item.get("type") or item.get("messageType") or "").lower()
    return t in {"function_call", "tool_call"}


def _is_tool_result(item: Mapping[str, Any]) -> bool:
    t = (item.get("type") or item.get("messageType") or "").lower()
    return t in {"function_call_output", "tool_result", "tool_output"}


def _call_id(item: Mapping[str, Any]) -> str | None:
    return item.get("call_id") or item.get("id") or item.get("tool_call_id")


def _tool_name(item: Mapping[str, Any]) -> str | None:
    raw = item.get("raw") or {}
    if isinstance(raw, Mapping):
        name = raw.get("name") or raw.get("tool_name")
        if isinstance(name, str):
            return name
    name = item.get("name") or item.get("tool_name")
    return name if isinstance(name, str) else None


@overload
def _compact_items(
    items: list[dict[str, Any]],
    *,
    trigger_turns: int | None,
    keep: int,
    clear_tool_inputs: bool,
    exclude_tools: Iterable[str],
    include_tools: Iterable[str] | None,
    force: bool = False,
    return_details: Literal[True],
) -> tuple[list[dict[str, Any]], Mapping[str, Any] | None]:
    ...


@overload
def _compact_items(
    items: list[dict[str, Any]],
    *,
    trigger_turns: int | None,
    keep: int,
    clear_tool_inputs: bool,
    exclude_tools: Iterable[str],
    include_tools: Iterable[str] | None,
    force: bool = False,
    return_details: Literal[False] = False,
) -> list[dict[str, Any]]:
    ...


def _compact_items(
    items: list[dict[str, Any]],
    *,
    trigger_turns: int | None,
    keep: int,
    clear_tool_inputs: bool,
    exclude_tools: Iterable[str],
    include_tools: Iterable[str] | None,
    force: bool = False,
    return_details: bool = False,
) -> tuple[list[dict[str, Any]], Mapping[str, Any] | None] | list[dict[str, Any]]:
    if not force and (trigger_turns is None or trigger_turns <= 0):
        return (items, None) if return_details else items

    turns = _group_by_turns(items)
    if not force and trigger_turns is not None and len(turns) <= trigger_turns:
        return (items, None) if return_details else items

    exclude = {t.lower() for t in exclude_tools}
    include = {t.lower() for t in include_tools} if include_tools else None
    protected_turns = {tuple(t) for t in turns[-max(1, keep) :]} if keep > 0 else set()
    indices_to_compact: set[int] = set()
    compacted_call_ids: list[str] = []
    compacted_tool_names: list[str] = []
    compacted_inputs = 0
    compacted_outputs = 0

    for turn in turns:
        if tuple(turn) in protected_turns:
            continue
        for idx in turn:
            item = items[idx]
            name = _tool_name(item)
            if name and name.lower() in exclude:
                continue
            if include is not None and name and name.lower() not in include:
                continue
            is_result = _is_tool_result(item)
            is_call = _is_tool_call(item)
            if is_result or (clear_tool_inputs and is_call):
                indices_to_compact.add(idx)
                call_id = _call_id(item)
                if call_id:
                    compacted_call_ids.append(str(call_id))
                tool_name = name or "tool"
                if tool_name:
                    compacted_tool_names.append(str(tool_name))
                if is_result:
                    compacted_outputs += 1
                elif is_call:
                    compacted_inputs += 1

    if not indices_to_compact:
        return (items, None) if return_details else items

    new_items: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if idx not in indices_to_compact:
            new_items.append(item)
            continue
        call_id = _call_id(item) or "unknown"
        name = _tool_name(item) or "tool"
        kind = "input" if _is_tool_call(item) and clear_tool_inputs else "output"
        placeholder = _placeholder(kind=kind, name=name, call_id=call_id)
        new_item = dict(item)
        new_item["content"] = placeholder
        new_item["output"] = placeholder
        new_item["type"] = "function_call_output"
        new_item["compacted"] = True
        new_items.append(new_item)
    if not return_details:
        return new_items

    details = {
        "strategy": "compact",
        "compacted_count": len(indices_to_compact),
        "compacted_call_ids": compacted_call_ids,
        "compacted_tool_names": compacted_tool_names,
        "compacted_inputs": compacted_inputs,
        "compacted_outputs": compacted_outputs,
        "keep_turns": keep,
        "trigger_turns": trigger_turns,
        "clear_tool_inputs": clear_tool_inputs,
        "excluded_tools": sorted(exclude) if exclude else [],
        "included_tools": sorted(include) if include else [],
        "total_items_before": len(items),
        "total_items_after": len(new_items),
        "turns_before": len(turns),
        "turns_after": len(_group_by_turns(new_items)),
    }
    return new_items, details


def _placeholder(*, kind: str, name: str, call_id: str) -> str:
    return f"⟦removed: tool {kind} for {name} (call_id={call_id}); reason=context_compaction⟧"


# Simple estimator used for telemetry and optional token budgets. This remains
# an approximation (chars/4) to avoid introducing a tokenizer dependency.
def estimate_tokens(item: Mapping[str, Any]) -> int:
    content = _collect_text([item])
    if not content:
        return 1
    return max(1, math.ceil(len(content) / 4))


def _estimate_total_tokens(items: Iterable[Mapping[str, Any]]) -> int:
    return sum(estimate_tokens(it) for it in items)


def _record_trigger(mode: MemoryStrategy, trigger: str) -> None:
    try:
        MEMORY_TRIGGER_TOTAL.labels(strategy=mode.value, trigger=trigger).inc()
    except Exception:
        # Best-effort metrics; never block runtime.
        pass


def _record_tokens(
    mode: MemoryStrategy,
    trigger: str | None,
    tokens_before: int,
    items_after: Sequence[Mapping[str, Any]],
) -> None:
    try:
        MEMORY_TOKENS_BEFORE_AFTER.labels(
            strategy=mode.value,
            trigger=trigger or "turns",
        ).observe(tokens_before)
        MEMORY_TOKENS_BEFORE_AFTER.labels(
            strategy=mode.value,
            trigger=trigger or "turns",
        ).observe(_estimate_total_tokens(items_after))
    except Exception:
        pass


__all__ = [
    "MemoryStrategy",
    "MemoryStrategyConfig",
    "StrategySession",
    "Summarizer",
    "NoopSummarizer",
    "estimate_tokens",
]
