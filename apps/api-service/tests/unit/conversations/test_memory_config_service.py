import pytest

from app.domain.conversations import ConversationMemoryConfig
from app.services.conversation_service import ConversationService
from tests.conftest import EphemeralConversationRepository


@pytest.mark.asyncio
async def test_set_and_get_memory_config_round_trip():
    repo = EphemeralConversationRepository()
    svc = ConversationService(repository=repo)
    conv_id = "conv-1"
    tenant_id = "tenant-1"

    cfg = ConversationMemoryConfig(
        strategy="summarize",
        max_user_turns=5,
        keep_last_turns=2,
        compact_trigger_turns=None,
        compact_keep=None,
        clear_tool_inputs=True,
        memory_injection=True,
    )

    await svc.set_memory_config(
        conv_id,
        tenant_id=tenant_id,
        config=cfg,
        provided_fields={
            "mode",
            "max_user_turns",
            "keep_last_turns",
            "clear_tool_inputs",
            "memory_injection",
        },
    )

    stored = await svc.get_memory_config(conv_id, tenant_id=tenant_id)
    assert stored is not None
    assert stored.strategy == "summarize"
    assert stored.max_user_turns == 5
    assert stored.keep_last_turns == 2
    assert stored.memory_injection is True
