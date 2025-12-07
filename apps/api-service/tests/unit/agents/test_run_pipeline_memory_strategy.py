from app.api.v1.chat.schemas import AgentChatRequest, MemoryStrategyRequest
from app.infrastructure.providers.openai.memory import MemoryStrategy
from app.services.agents.run_pipeline import (
    build_memory_strategy_config,
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


def test_resolve_memory_injection_precedence():
    req = AgentChatRequest(message="hi", memory_injection=None)
    conv_defaults = {"memory_injection": True}
    agent_defaults = {"memory_injection": False}
    assert resolve_memory_injection(req, conversation_defaults=conv_defaults, agent_defaults=agent_defaults)

    req2 = AgentChatRequest(message="hi", memory_injection=False)
    assert resolve_memory_injection(req2, conversation_defaults=conv_defaults, agent_defaults=agent_defaults) is False
