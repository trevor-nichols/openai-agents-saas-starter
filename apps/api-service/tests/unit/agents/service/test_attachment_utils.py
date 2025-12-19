import uuid

from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid as persistence_coerce_conversation_uuid,
)
from app.services.agents.attachment_utils import coerce_conversation_uuid


def test_coerce_conversation_uuid_matches_persistence_for_non_uuid() -> None:
    conversation_id = "external-conversation-123"

    assert coerce_conversation_uuid(conversation_id) == persistence_coerce_conversation_uuid(
        conversation_id
    )


def test_coerce_conversation_uuid_allows_none() -> None:
    assert coerce_conversation_uuid(None) is None


def test_coerce_conversation_uuid_passes_through_uuid() -> None:
    conversation_id = str(uuid.uuid4())

    assert coerce_conversation_uuid(conversation_id) == uuid.UUID(conversation_id)
