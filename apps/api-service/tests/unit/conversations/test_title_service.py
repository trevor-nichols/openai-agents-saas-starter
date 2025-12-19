from __future__ import annotations

from unittest.mock import ANY, AsyncMock

import pytest

from app.services.conversations.title_service import TitleService


class _RawDelta:
    def __init__(self, *, event_type: str, delta: str) -> None:
        self.type = event_type
        self.delta = delta


class _RawResponseEvent:
    def __init__(self, delta: str) -> None:
        self.type = "raw_response_event"
        self.data = _RawDelta(event_type="response.output_text.delta", delta=delta)


class _FakeStream:
    def __init__(self, *, deltas: list[str], final_output: object) -> None:
        self._deltas = deltas
        self.final_output = final_output

    async def stream_events(self):
        for delta in self._deltas:
            yield _RawResponseEvent(delta)


@pytest.mark.asyncio
async def test_stream_title_yields_title_chars_and_persists():
    conversation_service = AsyncMock()
    conversation_service.set_display_name = AsyncMock(return_value=True)

    def runner(_agent, _message: str):
        # Simulate JSON structured output streaming.
        return _FakeStream(
            deltas=['{"title":"Hel', 'lo World"}'],
            final_output={"title": "Hello World"},
        )

    svc = TitleService(conversation_service, stream_runner=runner)

    chunks: list[str] = []
    async for chunk in svc.stream_title(
        conversation_id="conv-1",
        tenant_id="tenant-1",
        first_user_message="hi",
    ):
        chunks.append(chunk)

    assert "".join(chunks) == "Hello World"
    conversation_service.set_display_name.assert_awaited_once_with(
        "conv-1",
        tenant_id="tenant-1",
        display_name="Hello World",
        generated_at=ANY,
    )


@pytest.mark.asyncio
async def test_stream_title_noops_for_empty_message():
    conversation_service = AsyncMock()
    runner = AsyncMock()

    svc = TitleService(conversation_service, stream_runner=runner)

    chunks: list[str] = []
    async for chunk in svc.stream_title(
        conversation_id="conv-1",
        tenant_id="tenant-1",
        first_user_message="   ",
    ):
        chunks.append(chunk)

    assert chunks == []
    runner.assert_not_called()
    conversation_service.set_display_name.assert_not_called()

