import uuid
import pytest
from datetime import datetime

from app.domain.conversations import ConversationAttachment, ConversationMessage, ConversationMetadata
from app.infrastructure.persistence.conversations.postgres import PostgresConversationRepository
from app.infrastructure.db import get_async_sessionmaker, get_engine
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_repo_roundtrip_with_attachments(monkeypatch):
    settings = get_settings()
    engine = get_engine()
    if engine is None:
        pytest.skip("engine not initialised")
    repo = PostgresConversationRepository(get_async_sessionmaker())

    tenant_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())
    meta = ConversationMetadata(
        tenant_id=tenant_id,
        agent_entrypoint="triage",
        provider="openai",
        provider_conversation_id=None,
        active_agent="triage",
        user_id=str(uuid.uuid4()),
        sdk_session_id="sess1",
    )
    msg = ConversationMessage(
        role="assistant",
        content="here is your image",
        timestamp=datetime.utcnow(),
        attachments=[
            ConversationAttachment(
                object_id=str(uuid.uuid4()),
                filename="image.png",
                mime_type="image/png",
                size_bytes=123,
                presigned_url=None,
                tool_call_id="tc1",
            )
        ],
    )

    await repo.add_message(conv_id, msg, tenant_id=tenant_id, metadata=meta)
    fetched = await repo.get_messages(conv_id, tenant_id=tenant_id)
    assert fetched[0].attachments
    att = fetched[0].attachments[0]
    assert att.filename == "image.png"
    assert att.tool_call_id == "tc1"
