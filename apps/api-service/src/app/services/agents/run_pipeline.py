"""Shared orchestration helpers for agent runs.

These utilities keep AgentService lean by centralizing the pre/post run
work (session prep, message persistence, telemetry projection). They are
intentionally side-effect free beyond the collaborators passed in, so they
stay easy to unit test.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
import uuid
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.infrastructure.providers.openai.memory import MemoryStrategy, MemoryStrategyConfig
from app.infrastructure.providers.openai.memory.summarizer import OpenAISummarizer
from app.observability.metrics import (
    MEMORY_COMPACTION_ITEMS_TOTAL,
    MEMORY_SUMMARY_INJECTION_TOTAL,
)
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.session_manager import SessionManager
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
_SUMMARY_MAX_AGE_SECONDS = 14 * 24 * 60 * 60
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


@dataclass(slots=True)
class RunContext:
    actor: ConversationActorContext
    provider: Any
    descriptor: Any
    conversation_id: str
    session_id: str
    session_handle: Any
    provider_conversation_id: str | None
    runtime_ctx: Any
    pre_session_items: list[dict[str, Any]]
    existing_state: Any
    compaction_events: list[AgentStreamEvent]


async def prepare_run_context(
    *,
    actor: ConversationActorContext,
    request: AgentChatRequest,
    provider_registry: AgentProviderRegistry,
    interaction_builder: InteractionContextBuilder,
    conversation_service: ConversationService,
    session_manager: SessionManager,
    provider_conversation_id: str | None = None,
    conversation_memory: Any | None = None,
    compaction_emitter: Callable[[AgentStreamEvent], Awaitable[None]] | None = None,
) -> RunContext:
    """Resolve provider + session state used by both sync and streaming flows."""

    provider = provider_registry.get_default()
    descriptor = provider.resolve_agent(request.agent_type)
    conversation_id = request.conversation_id or str(uuid.uuid4())

    runtime_ctx = await interaction_builder.build(
        actor=actor,
        request=request,
        conversation_id=conversation_id,
        agent_keys=[descriptor.key],
    )
    compaction_events: list[AgentStreamEvent] = []
    conversation_defaults = _memory_cfg_to_mapping(conversation_memory)
    memory_cfg = build_memory_strategy_config(
        request,
        conversation_defaults=conversation_defaults,
        agent_defaults=getattr(descriptor, "memory_strategy_defaults", None),
    )
    # Cross-session memory injection (prompt-level)
    inject_memory = resolve_memory_injection(
        request,
        conversation_defaults=conversation_defaults,
        agent_defaults=getattr(descriptor, "memory_strategy_defaults", None),
    )
    if inject_memory and request.conversation_id:
        summary_text = await _load_cross_session_summary(
            conversation_id=request.conversation_id,
            tenant_id=actor.tenant_id,
            agent_key=descriptor.key,
            conversation_service=conversation_service,
            max_age_seconds=_SUMMARY_MAX_AGE_SECONDS,
            max_chars=(memory_cfg.summary_max_chars if memory_cfg else 4000),
        )
        if summary_text:
            runtime_ctx.memory_summary = summary_text
    existing_state = await conversation_service.get_session_state(
        conversation_id, tenant_id=actor.tenant_id
    )

    async def _on_compaction(payload: Mapping[str, Any]) -> None:
        event = AgentStreamEvent(
            kind="lifecycle",
            event="memory_compaction",
            run_item_type="memory_compaction",
            agent=descriptor.key,
            conversation_id=conversation_id,
            payload=dict(payload),
        )
        if compaction_emitter:
            await compaction_emitter(event)
        compaction_events.append(event)
        try:
            inputs = int(payload.get("compacted_inputs", 0))
            outputs = int(payload.get("compacted_outputs", 0))
            if inputs:
                MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="input").inc(inputs)
            if outputs:
                MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="output").inc(outputs)
        except Exception:
            pass

    session_id, session_handle = await session_manager.acquire_session(
        provider,
        actor.tenant_id,
        conversation_id,
        provider_conversation_id,
        memory_strategy=memory_cfg,
        agent_key=descriptor.key,
        on_compaction=(
            _on_compaction if memory_cfg and memory_cfg.mode == MemoryStrategy.COMPACT else None
        ),
    )

    pre_session_items = await get_session_items(session_handle)

    return RunContext(
        actor=actor,
        provider=provider,
        descriptor=descriptor,
        conversation_id=conversation_id,
        session_id=session_id,
        session_handle=session_handle,
        provider_conversation_id=provider_conversation_id,
        runtime_ctx=runtime_ctx,
        pre_session_items=pre_session_items,
        existing_state=existing_state,
        compaction_events=compaction_events,
    )


async def record_user_message(
    *,
    ctx: RunContext,
    request: AgentChatRequest,
    conversation_service: ConversationService,
) -> ConversationMetadata:
    """Persist the inbound user message with consistent metadata."""

    metadata = build_metadata(
        tenant_id=ctx.actor.tenant_id,
        provider=ctx.provider.name,
        provider_conversation_id=ctx.provider_conversation_id,
        agent_entrypoint=request.agent_type or ctx.descriptor.key,
        active_agent=ctx.descriptor.key,
        session_id=ctx.session_id,
        user_id=ctx.actor.user_id,
    )
    user_message = ConversationMessage(role="user", content=request.message)
    await conversation_service.append_message(
        ctx.conversation_id,
        user_message,
        tenant_id=ctx.actor.tenant_id,
        metadata=metadata,
    )

    if hasattr(conversation_service, "record_conversation_created"):
        await conversation_service.record_conversation_created(
            ctx.conversation_id,
            tenant_id=ctx.actor.tenant_id,
            agent_entrypoint=request.agent_type or ctx.descriptor.key,
            existed=ctx.existing_state is not None,
        )

    return metadata


async def persist_assistant_message(
    *,
    ctx: RunContext,
    conversation_service: ConversationService,
    response_text: str,
    attachments,
    active_agent: str | None = None,
    handoff_count: int | None = None,
) -> None:
    """Store assistant response with aligned metadata."""

    agent_name = active_agent or ctx.descriptor.key
    assistant_message = ConversationMessage(
        role="assistant",
        content=response_text,
        attachments=attachments,
    )
    await conversation_service.append_message(
        ctx.conversation_id,
        assistant_message,
        tenant_id=ctx.actor.tenant_id,
        metadata=build_metadata(
            tenant_id=ctx.actor.tenant_id,
            provider=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
            agent_entrypoint=ctx.descriptor.key,
            active_agent=agent_name,
            session_id=ctx.session_id,
            user_id=ctx.actor.user_id,
            handoff_count=handoff_count,
        ),
    )


async def project_new_session_items(
    *,
    event_projector: EventProjector,
    session_handle: Any,
    pre_items: list[dict[str, Any]],
    conversation_id: str,
    tenant_id: str,
    agent: str | None,
    model: str | None,
    response_id: str | None,
    workflow_run_id: str | None = None,
) -> None:
    """Ingest newly created session items into the event log (best-effort)."""

    post_items = await get_session_items(session_handle)
    if not post_items:
        return

    delta = _compute_session_delta(pre_items, post_items)
    if not delta:
        if len(post_items) != len(pre_items):
            logging.getLogger(__name__).debug(
                "session_delta_empty_after_rewrite",
                extra={
                    "pre_len": len(pre_items),
                    "post_len": len(post_items),
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                },
            )
        return
    try:
        await event_projector.ingest_session_items(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            session_items=delta,
            agent=agent,
            model=model,
            response_id=response_id,
            workflow_run_id=workflow_run_id,
        )
    except Exception:  # pragma: no cover - defensive, best-effort
        logging.getLogger(__name__).exception(
            "event_projection_failed",
            extra={
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "agent": agent,
            },
        )


def build_metadata(
    *,
    tenant_id: str,
    provider: str | None,
    provider_conversation_id: str | None,
    agent_entrypoint: str,
    active_agent: str,
    session_id: str,
    user_id: str,
    handoff_count: int | None = None,
) -> ConversationMetadata:
    return ConversationMetadata(
        tenant_id=tenant_id,
        provider=provider,
        provider_conversation_id=provider_conversation_id,
        agent_entrypoint=agent_entrypoint,
        active_agent=active_agent,
        handoff_count=handoff_count,
        sdk_session_id=session_id,
        user_id=user_id,
    )


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
        logging.getLogger(__name__).exception(
            "session_items_fetch_failed",
        )
        return []


__all__ = [
    "RunContext",
    "prepare_run_context",
    "record_user_message",
    "persist_assistant_message",
    "project_new_session_items",
    "build_metadata",
    "get_session_items",
    "_compute_session_delta",
    "build_memory_strategy_config",
    "_memory_cfg_to_mapping",
]


def build_memory_strategy_config(
    request: AgentChatRequest,
    *,
    conversation_defaults: Mapping[str, Any] | None,
    agent_defaults: Mapping[str, Any] | None,
) -> MemoryStrategyConfig | None:
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


async def _load_cross_session_summary(
    *,
    conversation_id: str,
    tenant_id: str,
    agent_key: str | None,
    conversation_service: ConversationService,
    max_age_seconds: int,
    max_chars: int,
) -> str | None:
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


def _memory_cfg_to_mapping(cfg: Any) -> dict[str, Any] | None:
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


def _compute_session_delta(
    pre_items: Iterable[Mapping[str, Any]], post_items: Iterable[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """Return post items that are new or rewritten vs pre.

    StrategySession rewrites history (clear + re-add). We diff by fingerprint
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
