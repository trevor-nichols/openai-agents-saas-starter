from __future__ import annotations

from unittest.mock import ANY, AsyncMock

import pytest

from app.services.conversations import title_service as title_service_module
from app.services.conversations.title_service import TitleService


@pytest.mark.asyncio
async def test_generate_if_absent_persists_title_and_publishes_event(monkeypatch: pytest.MonkeyPatch):
    conversation_service = AsyncMock()
    conversation_service.set_display_name = AsyncMock(return_value=True)

    publish_mock = AsyncMock()
    monkeypatch.setattr(title_service_module.metadata_stream, "publish", publish_mock)

    async def runner(agent, message: str):
        class FakeResult:
            final_output = {"title": "Hello World!"}

        return FakeResult()

    svc = TitleService(conversation_service, runner=runner)
    title = await svc.generate_if_absent(
        conversation_id="conv-1",
        tenant_id="tenant-1",
        first_user_message="hi",
    )

    assert title == "Hello World"
    conversation_service.set_display_name.assert_awaited_once_with(
        "conv-1",
        tenant_id="tenant-1",
        display_name="Hello World",
        generated_at=ANY,
    )
    publish_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_if_absent_noops_when_title_already_set(monkeypatch: pytest.MonkeyPatch):
    conversation_service = AsyncMock()
    conversation_service.set_display_name = AsyncMock(return_value=False)

    publish_mock = AsyncMock()
    monkeypatch.setattr(title_service_module.metadata_stream, "publish", publish_mock)

    async def runner(agent, message: str):
        class FakeResult:
            final_output = {"title": "Some Title"}

        return FakeResult()

    svc = TitleService(conversation_service, runner=runner)
    title = await svc.generate_if_absent(
        conversation_id="conv-1",
        tenant_id="tenant-1",
        first_user_message="hi",
    )

    assert title is None
    conversation_service.set_display_name.assert_awaited_once()
    publish_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_if_absent_returns_none_for_empty_message():
    conversation_service = AsyncMock()
    runner = AsyncMock()

    svc = TitleService(conversation_service, runner=runner)
    title = await svc.generate_if_absent(
        conversation_id="conv-1",
        tenant_id="tenant-1",
        first_user_message="   ",
    )

    assert title is None
    runner.assert_not_called()
    conversation_service.set_display_name.assert_not_called()

