import asyncio

import pytest
from collections.abc import AsyncIterator

from agents.extensions.memory import SQLAlchemySession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.infrastructure.providers.openai.memory.strategy import (
    MemoryStrategy,
    MemoryStrategyConfig,
    StrategySession,
    Summarizer,
)


class _EchoSummarizer(Summarizer):
    async def summarize(self, text: str) -> str:
        return f"summary:{text.strip()}"


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield eng
    await eng.dispose()


def _session(engine: AsyncEngine, name: str = "s") -> SQLAlchemySession:
    return SQLAlchemySession(
        session_id=name,
        engine=engine,
        create_tables=True,
        sessions_table=f"sdk_{name}_sessions",
        messages_table=f"sdk_{name}_messages",
    )


def _turn(user: str, assistant: str) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": user, "type": "message"},
        {"role": "assistant", "content": assistant, "type": "message"},
    ]


@pytest.mark.asyncio
async def test_trim_keeps_tail(engine: AsyncEngine):
    base = _session(engine, "trim")
    session = StrategySession(
        base,
        MemoryStrategyConfig(
            mode=MemoryStrategy.TRIM,
            max_user_turns=3,
            keep_last_user_turns=2,
        ),
    )

    items = _turn("u1", "a1") + _turn("u2", "a2") + _turn("u3", "a3") + _turn("u4", "a4")
    await session.add_items(items)

    stored = await session.get_items()
    # Expect only last two user turns (u3/a3, u4/a4)
    assert [it["content"] for it in stored if it["role"] == "user"] == ["u3", "u4"]
    assert len(stored) == 4


@pytest.mark.asyncio
async def test_compact_replaces_old_tool_results(engine: AsyncEngine):
    base = _session(engine, "compact")
    session = StrategySession(
        base,
        MemoryStrategyConfig(
            mode=MemoryStrategy.COMPACT,
            compact_trigger_turns=1,
            compact_keep=1,
            compact_clear_tool_inputs=False,
        ),
    )

    items = [
        {"role": "user", "content": "u1"},
        {"type": "function_call", "name": "weather", "call_id": "c1"},
        {"type": "function_call_output", "call_id": "c1", "content": "sunny"},
        {"role": "user", "content": "u2"},
        {"type": "function_call_output", "call_id": "c2", "content": "cloudy"},
        {"role": "assistant", "content": "done"},
    ]

    await session.add_items(items)
    stored = await session.get_items()

    # Oldest turn (u1 + tool) should be compacted, latest turn untouched
    first_tool = stored[2]
    assert first_tool.get("compacted") is True
    assert "removed:" in first_tool.get("content", "")
    assert "tool output" in first_tool.get("content", "")

    # Last turn's result should remain intact
    last_tool = stored[4]
    assert last_tool.get("content") == "cloudy"


@pytest.mark.asyncio
async def test_summarize_injects_summary_and_keeps_tail(engine: AsyncEngine):
    base = _session(engine, "summ")
    session = StrategySession(
        base,
        MemoryStrategyConfig(
            mode=MemoryStrategy.SUMMARIZE,
            max_user_turns=2,
            keep_last_user_turns=1,
            summarizer=_EchoSummarizer(),
            summary_prefix="[summary]",
        ),
    )

    items = _turn("u1", "a1") + _turn("u2", "a2") + _turn("u3", "a3")
    await session.add_items(items)
    stored = await session.get_items()

    # Expect two summary items + last turn
    assert stored[0]["role"] == "user"
    assert stored[1]["role"] == "assistant"
    assert stored[1]["content"].startswith("summary:")
    assert [it["content"] for it in stored if it["role"] == "user"][-1] == "u3"
    assert len([it for it in stored if it.get("role") == "user"]) == 2


@pytest.mark.asyncio
async def test_compact_token_budget_forces_compaction(engine: AsyncEngine):
    base = _session(engine, "compact_tokens")
    session = StrategySession(
        base,
        MemoryStrategyConfig(
            mode=MemoryStrategy.COMPACT,
            compact_trigger_turns=10,  # high on purpose
            compact_keep=1,
            token_budget=5,  # low budget to force compaction by tokens
        ),
    )

    items = [
        {"role": "user", "content": "u1"},
        {"type": "function_call_output", "call_id": "c1", "content": "A" * 200},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "ok"},
    ]

    await session.add_items(items)
    stored = await session.get_items()

    # Despite trigger_turns not being reached, token budget should compact the tool output
    assert any(it.get("compacted") and it.get("call_id") == "c1" for it in stored)


@pytest.mark.asyncio
async def test_compact_replaces_inputs_and_outputs(engine: AsyncEngine):
    base = _session(engine, "compact_io")
    session = StrategySession(
        base,
        MemoryStrategyConfig(
            mode=MemoryStrategy.COMPACT,
            compact_trigger_turns=1,
            compact_keep=1,
            compact_clear_tool_inputs=True,
            compact_include_tools=frozenset({"weather"}),
        ),
    )

    items = [
        {"role": "user", "content": "u1"},
        {"type": "function_call", "name": "weather", "call_id": "c1"},
        {"type": "function_call_output", "call_id": "c1", "content": "sunny"},
        {"role": "user", "content": "u2"},
        {"type": "function_call_output", "call_id": "c2", "content": "cloudy"},
        {"role": "assistant", "content": "done"},
    ]

    await session.add_items(items)
    stored = await session.get_items()

    # First turn tool call should be compacted as input; output too
    first_call = stored[1]
    first_out = stored[2]
    assert first_call.get("compacted") is True
    assert "input" in first_call.get("content", "")
    assert first_out.get("compacted") is True
    assert "output" in first_out.get("content", "")

    # Second tool output (not included) stays intact
    assert stored[4].get("content") == "cloudy"
