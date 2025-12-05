from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents._shared.specs import AgentSpec, HandoffConfig
from app.core.settings import Settings
from app.infrastructure.providers.openai.registry import OpenAIAgentRegistry


def _settings_factory():
    # Minimal settings; defaults cover required fields
    return Settings(openai_api_key="test-key")


def _conversation_searcher(tenant_id: str, query: str):
    return SimpleNamespace(items=[])


@pytest.mark.asyncio
async def test_handoff_override_defaults_enabled(monkeypatch: pytest.MonkeyPatch):
    specs = [
        AgentSpec(
            key="b",
            display_name="B",
            description="target",
            instructions="hi",
        ),
        AgentSpec(
            key="a",
            display_name="A",
            description="source",
            instructions="hi",
            handoff_keys=("b",),
            handoff_overrides={"b": HandoffConfig(tool_name="to-b")},
        ),
    ]

    registry = OpenAIAgentRegistry(
        settings_factory=_settings_factory,
        conversation_searcher=_conversation_searcher,
        specs=specs,
    )

    agent = registry.get_agent_handle("a", validate_prompts=False)
    assert agent is not None
    assert agent.handoffs, "handoff should exist when override has no is_enabled"
    handoff = agent.handoffs[0]
    assert getattr(handoff, "is_enabled", False) is True
    assert getattr(handoff, "tool_name", None) == "to-b"
