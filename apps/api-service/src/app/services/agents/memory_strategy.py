"""Memory strategy resolution and cross-session prompt injection.

This module keeps `run_pipeline` focused on orchestration concerns by extracting:
- Memory strategy config precedence resolution (request > conversation > agent).
- Cross-session summary injection controls.

These helpers are intentionally deterministic and side-effect free beyond the
collaborators passed in (ConversationService, metrics).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from app.api.v1.chat.schemas import AgentChatRequest
from app.infrastructure.providers.openai.memory import MemoryStrategy, MemoryStrategyConfig
from app.infrastructure.providers.openai.memory.summarizer import OpenAISummarizer
from app.observability.metrics import MEMORY_SUMMARY_INJECTION_TOTAL
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_MAX_AGE_SECONDS = 14 * 24 * 60 * 60

_ALLOWED_MEMORY_KEYS = {
    "mode",
    "strategy",
    "memory_strategy",
    "token_budget",
    "token_soft_budget",
    "token_remaining_pct",
    "token_soft_remaining_pct",
    "context_window_tokens",
    "max_user_turns",
    "keep_last_user_turns",
    "keep_last_turns",
    "compact_trigger_turns",
    "compact_keep",
    "compact_clear_tool_inputs",
    "clear_tool_inputs",
    "compact_exclude_tools",
    "exclude_tools",
    "compact_include_tools",
    "include_tools",
    "summarizer_model",
    "summary_max_tokens",
    "summary_max_chars",
    "memory_injection",
}


def build_memory_strategy_config(
    request: AgentChatRequest,
    *,
    conversation_defaults: Mapping[str, Any] | None,
    agent_defaults: Mapping[str, Any] | None,
) -> MemoryStrategyConfig | None:
    """Resolve the effective memory strategy config for a run."""

    # Precedence: request > conversation > agent > none
    if request.memory_strategy:
        cfg_req = _config_from_request(request.memory_strategy)
        _apply_token_thresholds(cfg_req)
        _ensure_summarizer(cfg_req)
        return cfg_req
    if conversation_defaults:
        cfg_conv = _config_from_mapping(conversation_defaults)
        if cfg_conv:
            _apply_token_thresholds(cfg_conv)
            _ensure_summarizer(cfg_conv)
            return cfg_conv
    if agent_defaults:
        cfg_agent = _config_from_mapping(agent_defaults)
        if cfg_agent:
            _apply_token_thresholds(cfg_agent)
            _ensure_summarizer(cfg_agent)
        return cfg_agent
    return None


def resolve_memory_injection(
    request: AgentChatRequest,
    *,
    conversation_defaults: Mapping[str, Any] | None,
    agent_defaults: Mapping[str, Any] | None,
) -> bool:
    """Resolve whether cross-session summary injection should occur."""

    if request.memory_injection is not None:
        return bool(request.memory_injection)

    if conversation_defaults is not None and "memory_injection" in conversation_defaults:
        val = conversation_defaults.get("memory_injection")
        if val is not None:
            return bool(val)

    if agent_defaults is not None and "memory_injection" in agent_defaults:
        val = agent_defaults.get("memory_injection")
        return bool(val) if val is not None else False

    return False


async def load_cross_session_summary(
    *,
    conversation_id: str,
    tenant_id: str,
    agent_key: str | None,
    conversation_service: ConversationService,
    max_age_seconds: int,
    max_chars: int,
) -> str | None:
    """Fetch the latest persisted summary, applying age/size constraints."""

    summary_row = await conversation_service.get_latest_summary(
        conversation_id,
        tenant_id=tenant_id,
        agent_key=agent_key,
        max_age_seconds=max_age_seconds,
    )
    if summary_row is None:
        return None

    summary_text = getattr(summary_row, "summary_text", None)
    if not summary_text:
        return None

    created_at_raw = getattr(summary_row, "created_at", None)

    def _to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    created_at = _to_utc(created_at_raw)
    if max_age_seconds and created_at is not None:
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        if created_at < cutoff:
            logger.info(
                "memory.injection.summary_skipped",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "agent_key": agent_key,
                    "reason": "stale",
                    "created_at": created_at.isoformat(),
                },
            )
            try:
                MEMORY_SUMMARY_INJECTION_TOTAL.labels(result="stale").inc()
            except Exception:
                pass
            return None

    if max_chars > 0 and len(summary_text) > max_chars:
        logger.info(
            "memory.injection.summary_skipped",
            extra={
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "agent_key": agent_key,
                "reason": "too_long",
                "length": len(summary_text),
                "max_chars": max_chars,
            },
        )
        try:
            MEMORY_SUMMARY_INJECTION_TOTAL.labels(result="too_long").inc()
        except Exception:
            pass
        return None

    logger.info(
        "memory.injection.summary_used",
        extra={
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "agent_key": agent_key,
            "length": len(summary_text),
            "created_at": created_at.isoformat() if created_at else None,
        },
    )
    try:
        MEMORY_SUMMARY_INJECTION_TOTAL.labels(result="used").inc()
    except Exception:
        pass
    return summary_text


def memory_cfg_to_mapping(cfg: Any) -> dict[str, Any] | None:
    """Best-effort conversion of persisted memory config objects into a mapping."""

    if cfg is None:
        return None
    if isinstance(cfg, Mapping):
        return dict(cfg)
    # Support dataclass-like objects (ConversationMemoryConfig)
    fields = (
        "strategy",
        "max_user_turns",
        "keep_last_turns",
        "compact_trigger_turns",
        "compact_keep",
        "clear_tool_inputs",
        "token_budget",
        "token_soft_budget",
        "memory_injection",
    )
    result: dict[str, Any] = {}
    for key in fields:
        if hasattr(cfg, key):
            result[key] = getattr(cfg, key)
    return result


def _config_from_request(ms: Any) -> MemoryStrategyConfig:
    mode = MemoryStrategy(ms.mode)
    keep_last = ms.keep_last_user_turns if ms.keep_last_user_turns is not None else 0
    config = MemoryStrategyConfig(mode=mode)
    config.token_budget = ms.token_budget
    config.token_soft_budget = ms.token_soft_budget
    config.token_remaining_pct = getattr(ms, "token_remaining_pct", None)
    config.token_soft_remaining_pct = getattr(ms, "token_soft_remaining_pct", None)
    context_window = getattr(ms, "context_window_tokens", None)
    if context_window is not None:
        config.context_window_tokens = context_window
    config.summarizer_model = getattr(ms, "summarizer_model", None)
    summary_tokens = getattr(ms, "summary_max_tokens", None)
    if summary_tokens is not None:
        config.summary_max_tokens = max(1, int(summary_tokens))
    summary_chars = getattr(ms, "summary_max_chars", None)
    if summary_chars is not None:
        config.summary_max_chars = max(1, int(summary_chars))
    if mode in {MemoryStrategy.TRIM, MemoryStrategy.SUMMARIZE}:
        config.max_user_turns = ms.max_user_turns
        config.keep_last_user_turns = max(0, keep_last)
    if mode == MemoryStrategy.COMPACT:
        config.compact_trigger_turns = ms.compact_trigger_turns
        if ms.compact_keep is None:
            config.compact_keep = 2
        else:
            config.compact_keep = 2 if ms.compact_keep < 0 else max(0, ms.compact_keep)
        config.compact_clear_tool_inputs = bool(ms.compact_clear_tool_inputs)
        if ms.compact_exclude_tools:
            config.compact_exclude_tools = frozenset(t.lower() for t in ms.compact_exclude_tools)
        if getattr(ms, "compact_include_tools", None):
            config.compact_include_tools = frozenset(t.lower() for t in ms.compact_include_tools)
    return config


def _config_from_mapping(data: Mapping[str, Any]) -> MemoryStrategyConfig | None:
    mode_value = data.get("mode") or data.get("strategy") or data.get("memory_strategy")
    if mode_value is None:
        return None
    _warn_on_unknown_keys(data, label="memory_strategy")
    try:
        mode = MemoryStrategy(str(mode_value).lower())
    except ValueError:
        return None

    config = MemoryStrategyConfig(mode=mode)
    config.token_budget = _maybe_int(data.get("token_budget"))
    config.token_soft_budget = _maybe_int(data.get("token_soft_budget"))
    token_remaining = data.get("token_remaining_pct")
    if token_remaining is not None:
        try:
            config.token_remaining_pct = float(token_remaining)
        except (TypeError, ValueError):
            pass
    token_soft_remaining = data.get("token_soft_remaining_pct")
    if token_soft_remaining is not None:
        try:
            config.token_soft_remaining_pct = float(token_soft_remaining)
        except (TypeError, ValueError):
            pass
    window = _maybe_int(data.get("context_window_tokens"))
    if window is not None:
        config.context_window_tokens = window
    config.max_user_turns = _maybe_int(data.get("max_user_turns"))
    keep_val = _maybe_int(data.get("keep_last_user_turns"))
    if keep_val is None:
        keep_val = _maybe_int(data.get("keep_last_turns"))
    config.keep_last_user_turns = max(0, keep_val) if keep_val is not None else 0
    config.compact_trigger_turns = _maybe_int(data.get("compact_trigger_turns"))
    if config.compact_trigger_turns is not None and config.compact_trigger_turns < 0:
        config.compact_trigger_turns = None
    keep_compact = _maybe_int(data.get("compact_keep"))
    if keep_compact is not None:
        config.compact_keep = 2 if keep_compact < 0 else max(0, keep_compact)
    clear_val = data.get("compact_clear_tool_inputs")
    if clear_val is None:
        clear_val = data.get("clear_tool_inputs")
    if clear_val is not None:
        config.compact_clear_tool_inputs = bool(clear_val)
    exclude = data.get("compact_exclude_tools") or data.get("exclude_tools")
    if exclude:
        config.compact_exclude_tools = frozenset(str(t).lower() for t in exclude)
    include = data.get("compact_include_tools") or data.get("include_tools")
    if include:
        config.compact_include_tools = frozenset(str(t).lower() for t in include)
    summarizer_model = data.get("summarizer_model")
    if isinstance(summarizer_model, str):
        config.summarizer_model = summarizer_model
    max_tokens = _maybe_int(data.get("summary_max_tokens"))
    if max_tokens is not None:
        config.summary_max_tokens = max(1, max_tokens)
    max_chars = _maybe_int(data.get("summary_max_chars"))
    if max_chars is not None:
        config.summary_max_chars = max(1, max_chars)
    return config


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _warn_on_unknown_keys(data: Mapping[str, Any], *, label: str) -> None:
    extra_keys = set(data.keys()) - _ALLOWED_MEMORY_KEYS
    if extra_keys:
        logging.getLogger(__name__).warning(
            "memory_strategy.unknown_keys",
            extra={"label": label, "unknown_keys": sorted(extra_keys)},
        )


def _apply_token_thresholds(cfg: MemoryStrategyConfig) -> None:
    """Derive absolute token budgets from percentage thresholds and defaults."""

    def _clamp_pct(value: float | None) -> float | None:
        try:
            return max(0.0, min(1.0, float(value))) if value is not None else None
        except (TypeError, ValueError):
            return None

    context_window = cfg.context_window_tokens or 400_000
    cfg.context_window_tokens = context_window

    if cfg.token_remaining_pct is None and cfg.token_budget is None:
        cfg.token_remaining_pct = 0.20

    pct = _clamp_pct(cfg.token_remaining_pct)
    if cfg.token_budget is None and pct is not None:
        cfg.token_remaining_pct = pct
        cfg.token_budget = max(0, int(context_window * (1 - pct)))

    soft_pct = _clamp_pct(cfg.token_soft_remaining_pct)
    if cfg.token_soft_budget is None and soft_pct is not None:
        cfg.token_soft_remaining_pct = soft_pct
        cfg.token_soft_budget = max(0, int(context_window * (1 - soft_pct)))

    if cfg.max_user_turns is not None and cfg.max_user_turns < 0:
        cfg.max_user_turns = None


def _ensure_summarizer(cfg: MemoryStrategyConfig) -> None:
    """Attach a production summarizer when needed."""

    if cfg.mode != MemoryStrategy.SUMMARIZE or cfg.summarizer is not None:
        return

    model = cfg.summarizer_model or "gpt-5.1"
    cfg.summarizer = OpenAISummarizer(
        model=model,
        max_tokens=cfg.summary_max_tokens,
        max_chars=cfg.summary_max_chars,
    )


__all__ = [
    "DEFAULT_SUMMARY_MAX_AGE_SECONDS",
    "build_memory_strategy_config",
    "load_cross_session_summary",
    "memory_cfg_to_mapping",
    "resolve_memory_injection",
]

