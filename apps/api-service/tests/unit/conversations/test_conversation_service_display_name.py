from __future__ import annotations

import pytest

from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.services.conversation_service import conversation_service


@pytest.mark.asyncio
async def test_update_display_name_normalizes_and_persists():
    tenant_id = "tenant-1"
    conversation_id = "conv-1"

    await conversation_service.append_message(
        conversation_id,
        ConversationMessage(role="user", content="hi"),
        tenant_id=tenant_id,
        metadata=ConversationMetadata(tenant_id=tenant_id, agent_entrypoint="triage"),
    )

    await conversation_service.update_display_name(
        conversation_id,
        tenant_id=tenant_id,
        display_name="  Hello\nWorld  ",
    )

    record = await conversation_service.get_conversation(conversation_id, tenant_id=tenant_id)
    assert record is not None
    assert record.display_name == "Hello World"


@pytest.mark.asyncio
async def test_update_display_name_rejects_empty():
    with pytest.raises(ValueError, match="display_name must not be empty"):
        await conversation_service.update_display_name(
            "conv-missing",
            tenant_id="tenant-1",
            display_name="   \n",
        )

