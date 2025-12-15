import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Tuple, cast

from app.api.v1.chat.schemas import AgentChatRequest, MemoryStrategyRequest
from app.infrastructure.providers.openai.memory import MemoryStrategy
from app.infrastructure.providers.openai.memory.strategy import (
    MemoryStrategyConfig,
    StrategySession,
)
from app.observability.metrics import (
    MEMORY_COMPACTION_ITEMS_TOTAL,
    MEMORY_SUMMARY_INJECTION_TOTAL,
    MEMORY_TOKENS_BEFORE_AFTER,
    MEMORY_TRIGGER_TOTAL,
)
from app.services.agents.memory_strategy import (
    build_memory_strategy_config,
    load_cross_session_summary,
    resolve_memory_injection,
)


def test_build_memory_strategy_config_trim():
    req = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(mode="trim", max_user_turns=5, keep_last_user_turns=2),
    )
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=None)
    assert cfg is not None
    assert cfg.mode == MemoryStrategy.TRIM
    assert cfg.max_user_turns == 5
    assert cfg.keep_last_user_turns == 2


def test_build_memory_strategy_config_compact_defaults():
    req = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(mode="compact", compact_trigger_turns=10),
    )
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=None)
    assert cfg is not None
    assert cfg.mode == MemoryStrategy.COMPACT
    assert cfg.compact_trigger_turns == 10
    assert cfg.compact_keep == 2  # default


def test_build_memory_strategy_config_falls_back_to_agent_defaults():
    req = AgentChatRequest(message="hi", memory_strategy=None)
    agent_defaults = {"mode": "trim", "max_user_turns": 3, "keep_last_turns": 1}
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=agent_defaults)
    assert cfg and cfg.mode == MemoryStrategy.TRIM
    assert cfg.max_user_turns == 3
    assert cfg.keep_last_user_turns == 1


def test_build_memory_strategy_config_clamps_pct_and_keep():
    req = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(
            mode="compact",
            token_remaining_pct=1.5,
            token_soft_remaining_pct=-0.5,
            compact_keep=-2,
        ),
    )
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=None)
    assert cfg is not None
    # Budgets are clamped/derived from pct
    assert cfg.token_budget == 0
    assert cfg.token_soft_budget == cfg.context_window_tokens  # -0.5 clamps to 0 -> full window
    assert cfg.compact_keep == 2  # default when negative provided


def test_resolve_memory_injection_precedence():
    req = AgentChatRequest(message="hi", memory_injection=None)
    conv_defaults = {"memory_injection": True}
    agent_defaults = {"memory_injection": False}
    assert resolve_memory_injection(req, conversation_defaults=conv_defaults, agent_defaults=agent_defaults)

    req2 = AgentChatRequest(message="hi", memory_injection=False)
    assert resolve_memory_injection(req2, conversation_defaults=conv_defaults, agent_defaults=agent_defaults) is False


def test_load_cross_session_summary_rejects_stale_and_long(monkeypatch):
    class _Row:
        def __init__(self, text: str, created_at):
            self.summary_text = text
            self.created_at = created_at

    class _Svc:
        def __init__(self, row):
            self._row = row

        async def get_latest_summary(self, conversation_id, *, tenant_id, agent_key, max_age_seconds):
            return self._row

    # stale
    stale_row = _Row("ok", datetime.utcnow() - timedelta(days=30))
    svc = _Svc(stale_row)
    res = asyncio.get_event_loop().run_until_complete(
        load_cross_session_summary(
            conversation_id="c",
            tenant_id="t",
            agent_key="a",
            conversation_service=svc,
            max_age_seconds=10,
            max_chars=100,
        )
    )
    assert res is None

    # too long
    long_row = _Row("x" * 200, datetime.utcnow())
    svc2 = _Svc(long_row)
    res2 = asyncio.get_event_loop().run_until_complete(
        load_cross_session_summary(
            conversation_id="c",
            tenant_id="t",
            agent_key="a",
            conversation_service=svc2,
            max_age_seconds=10,
            max_chars=10,
        )
    )
    assert res2 is None

    # timezone-aware created_at should not raise; returns summary
    aware_row = _Row("fresh", datetime.now(timezone.utc))
    svc3 = _Svc(aware_row)
    res3 = asyncio.get_event_loop().run_until_complete(
        load_cross_session_summary(
            conversation_id="c",
            tenant_id="t",
            agent_key="a",
            conversation_service=svc3,
            max_age_seconds=10,
            max_chars=100,
        )
    )
    assert res3 == "fresh"


def _reset_memory_metrics() -> None:
    for counter in (MEMORY_TRIGGER_TOTAL, MEMORY_SUMMARY_INJECTION_TOTAL, MEMORY_COMPACTION_ITEMS_TOTAL):
        c = cast(Any, counter)
        c._metrics.clear()
        if hasattr(c, "_value"):
            c._value.set(0)
    hist = cast(Any, MEMORY_TOKENS_BEFORE_AFTER)
    hist._metrics.clear()


def _counter_value(counter, labels: Tuple[str, ...]) -> int:
    metric = cast(Any, counter)._metrics.get(labels)
    if metric is None:
        return 0
    val = getattr(metric, "_value", None)
    return int(val.get()) if val is not None else 0


def _hist_count(hist, labels: Tuple[str, ...]) -> int:
    metric = cast(Any, hist)._metrics.get(labels)
    if metric is None:
        return 0
    buckets = getattr(metric, "_buckets", None)
    if not buckets:
        return 0
    return int(sum(b.get() for b in buckets))


def test_summary_injection_metrics_mark_stale_and_used(monkeypatch):
    _reset_memory_metrics()

    class _Row:
        def __init__(self, text: str, created_at):
            self.summary_text = text
            self.created_at = created_at

    class _Svc:
        def __init__(self, row):
            self._row = row

        async def get_latest_summary(self, conversation_id, *, tenant_id, agent_key, max_age_seconds):
            return self._row

    # stale
    stale_row = _Row("ok", datetime.utcnow() - timedelta(days=30))
    svc = _Svc(stale_row)
    res = asyncio.get_event_loop().run_until_complete(
        load_cross_session_summary(
            conversation_id="c",
            tenant_id="t",
            agent_key="a",
            conversation_service=svc,
            max_age_seconds=10,
            max_chars=100,
        )
    )
    assert res is None
    assert _counter_value(MEMORY_SUMMARY_INJECTION_TOTAL, ("stale",)) == 1

    # valid
    valid_row = _Row("fine", datetime.utcnow())
    svc_valid = _Svc(valid_row)
    res_valid = asyncio.get_event_loop().run_until_complete(
        load_cross_session_summary(
            conversation_id="c",
            tenant_id="t",
            agent_key="a",
            conversation_service=svc_valid,
            max_age_seconds=10,
            max_chars=100,
        )
    )
    assert res_valid == "fine"
    assert _counter_value(MEMORY_SUMMARY_INJECTION_TOTAL, ("used",)) == 1


def test_token_trigger_records_metrics_and_tokens(monkeypatch):
    _reset_memory_metrics()

    # Force summarize via token threshold
    req = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(
            mode="summarize",
            token_budget=1,  # tiny to force trigger
            keep_last_user_turns=1,
            max_user_turns=None,
        ),
    )
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=None)
    assert cfg

    # We simulate tokens by using two long items; expect trigger by token_budget
    items = [
        {"role": "user", "content": "x" * 100},
        {"role": "assistant", "content": "y" * 100},
        {"role": "user", "content": "z" * 100},
    ]

    class _DummySession:
        def __init__(self, data):
            self.items = list(data)

        async def get_items(self, limit=None):
            return list(self.items if limit is None else self.items[:limit])

        async def add_items(self, new_items):
            self.items.extend(new_items)

        async def clear_session(self):
            self.items.clear()

        async def pop_item(self):
            return None

    base = _DummySession(items)
    session = StrategySession(base, cfg, on_summary=None, on_compaction=None)
    start_count = _hist_count(MEMORY_TOKENS_BEFORE_AFTER, ("summarize", "token_budget"))
    asyncio.get_event_loop().run_until_complete(session.add_items([]))
    # Trigger counter should increment for summarize/token_budget
    assert _counter_value(MEMORY_TRIGGER_TOTAL, ("summarize", "token_budget")) >= 1

    # Tokens histogram should have recorded observations (before/after)
    assert _hist_count(MEMORY_TOKENS_BEFORE_AFTER, ("summarize", "token_budget")) > start_count


def test_token_soft_trigger_records_metrics_and_tokens(monkeypatch):
    _reset_memory_metrics()

    req = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(
            mode="summarize",
            token_soft_budget=1,  # tiny soft budget to force trigger
            keep_last_user_turns=1,
            max_user_turns=None,
        ),
    )
    cfg = build_memory_strategy_config(req, conversation_defaults=None, agent_defaults=None)
    assert cfg

    items = [
        {"role": "user", "content": "x" * 100},
        {"role": "assistant", "content": "y" * 100},
        {"role": "user", "content": "z" * 100},
    ]

    class _DummySession:
        def __init__(self, data):
            self.items = list(data)

        async def get_items(self, limit=None):
            return list(self.items if limit is None else self.items[:limit])

        async def add_items(self, new_items):
            self.items.extend(new_items)

        async def clear_session(self):
            self.items.clear()

        async def pop_item(self):
            return None

    base = _DummySession(items)
    session = StrategySession(base, cfg, on_summary=None, on_compaction=None)
    start_count = _hist_count(MEMORY_TOKENS_BEFORE_AFTER, ("summarize", "token_soft_budget"))
    asyncio.get_event_loop().run_until_complete(session.add_items([]))

    assert _counter_value(MEMORY_TRIGGER_TOTAL, ("summarize", "token_soft_budget")) >= 1
    assert _hist_count(MEMORY_TOKENS_BEFORE_AFTER, ("summarize", "token_soft_budget")) > start_count


def test_compaction_metrics_inputs_outputs(monkeypatch):
    _reset_memory_metrics()
    items = [
        {"role": "user", "content": "u1"},
        {"type": "function_call", "name": "weather", "call_id": "c1"},
        {"type": "function_call_output", "call_id": "c1", "content": "sunny"},
        {"role": "user", "content": "u2"},
        {"type": "function_call_output", "call_id": "c2", "content": "cloudy"},
    ]

    class _DummySession:
        def __init__(self, data):
            self.items = list(data)

        async def get_items(self, limit=None):
            return list(self.items if limit is None else self.items[:limit])

        async def add_items(self, new_items):
            self.items.extend(new_items)

        async def clear_session(self):
            self.items.clear()

        async def pop_item(self):
            return None

    cfg = MemoryStrategyConfig(
        mode=MemoryStrategy.COMPACT,
        compact_trigger_turns=1,
        compact_keep=1,
        compact_clear_tool_inputs=True,
        compact_include_tools=frozenset({"weather"}),
    )
    async def _emit(payload: dict[str, Any]) -> None:
        # mimic run_pipeline compaction emitter to bump metrics
        inputs = int(payload.get("compacted_inputs", 0))
        outputs = int(payload.get("compacted_outputs", 0))
        if inputs:
            MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="input").inc(inputs)
        if outputs:
            MEMORY_COMPACTION_ITEMS_TOTAL.labels(kind="output").inc(outputs)

    base = _DummySession(items)
    session = StrategySession(base, cfg, on_compaction=_emit)
    asyncio.get_event_loop().run_until_complete(session.add_items([]))

    assert _counter_value(MEMORY_COMPACTION_ITEMS_TOTAL, ("input",)) >= 1
    assert _counter_value(MEMORY_COMPACTION_ITEMS_TOTAL, ("output",)) >= 1
