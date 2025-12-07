import pytest

from app.infrastructure.providers.openai.memory.strategy import (
    MemoryStrategy,
    MemoryStrategyConfig,
    StrategySession,
)


class _FakeSession:
    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []

    async def get_items(self, limit=None):
        return list(self.items if limit is None else self.items[:limit])

    async def add_items(self, items):
        self.items.extend(items)

    async def clear_session(self):
        self.items.clear()

    async def pop_item(self):  # pragma: no cover - not used here
        if not self.items:
            return None
        return self.items.pop()


@pytest.mark.asyncio
async def test_strategy_session_emits_compaction_event():
    base = _FakeSession()
    cfg = MemoryStrategyConfig(
        mode=MemoryStrategy.COMPACT,
        compact_trigger_turns=1,
        compact_keep=1,
        compact_clear_tool_inputs=True,
    )

    events: list[dict] = []

    async def on_compaction(payload):
        events.append(payload)

    session = StrategySession(base, cfg, on_compaction=on_compaction)

    await session.add_items(
        [
            {"role": "user", "content": "hi", "type": "message"},
            {
                "role": "assistant",
                "type": "tool_output",
                "tool_call_id": "call-1",
                "name": "weather",
                "content": "rainy",
            },
        ]
    )

    # Compaction should have replaced tool output and fired callback
    assert len(events) == 1
    payload = events[0]
    assert payload["strategy"] == "compact"
    assert payload["compacted_count"] == 1
    assert payload["compacted_call_ids"] == ["call-1"]

    items = await base.get_items()
    assert len(items) == 2
    assert items[1].get("compacted") is True
    assert items[1].get("type") == "function_call_output"
