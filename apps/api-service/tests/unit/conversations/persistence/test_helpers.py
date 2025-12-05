"""Unit tests for conversation helper modules (ids, cursors, mappers)."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.domain.conversations import ConversationAttachment
from app.infrastructure.persistence.conversations import ids as ids_helpers
from app.infrastructure.persistence.conversations import cursors
from app.infrastructure.persistence.conversations import mappers
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage


def test_conversation_id_round_trip_uuid() -> None:
    raw = "6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"
    coerced = ids_helpers.coerce_conversation_uuid(raw)
    assert str(coerced) == raw
    derived = ids_helpers.derive_conversation_key(raw)
    assert derived == raw


def test_conversation_id_namespace_hash() -> None:
    original = "external-id-123"
    coerced = ids_helpers.coerce_conversation_uuid(original)
    derived = ids_helpers.derive_conversation_key(original)
    # Deterministic mapping, length preserved under 255 chars
    assert isinstance(coerced, UUID)
    assert derived == original


def test_conversation_key_rejects_long_value() -> None:
    oversized = "x" * 256
    with pytest.raises(ValueError):
        ids_helpers.derive_conversation_key(oversized)


def test_list_cursor_round_trip() -> None:
    ts = datetime.now(UTC)
    conv = UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14")
    cursor = cursors.encode_list_cursor(ts, conv)
    decoded_ts, decoded_conv = cursors.decode_list_cursor(cursor)
    assert decoded_conv == conv
    assert decoded_ts == ts


def test_search_cursor_round_trip() -> None:
    ts = datetime.now(UTC)
    conv = UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14")
    cursor = cursors.encode_search_cursor(0.42, ts, conv)
    rank, decoded_ts, decoded_conv = cursors.decode_search_cursor(cursor)
    assert rank == pytest.approx(0.42)
    assert decoded_conv == conv
    assert decoded_ts == ts


def test_decode_cursor_invalid_payload() -> None:
    bogus = base64.urlsafe_b64encode(json.dumps({"foo": "bar"}).encode()).decode()
    with pytest.raises(ValueError):
        cursors.decode_list_cursor(bogus)


def test_attachment_round_trip_serialization() -> None:
    attachment = ConversationAttachment(
        object_id="obj",
        filename="file.txt",
        mime_type="text/plain",
        size_bytes=10,
        tool_call_id="call-1",
    )
    encoded = mappers.serialize_attachments([attachment])
    assert encoded == [
        {
            "object_id": "obj",
            "filename": "file.txt",
            "mime_type": "text/plain",
            "size_bytes": 10,
            "tool_call_id": "call-1",
        }
    ]
    decoded = mappers.extract_attachments(encoded)
    assert decoded[0].filename == "file.txt"
    assert decoded[0].tool_call_id == "call-1"


def test_record_from_model_composes_messages() -> None:
    conv = AgentConversation(
        id=UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"),
        conversation_key="key-1",
        tenant_id=UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c"),
        agent_entrypoint="triage",
        message_count=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    msg = AgentMessage(
        conversation_id=conv.id,
        position=0,
        role="assistant",
        content={"text": "hi"},
        created_at=datetime.now(UTC),
    )
    record = mappers.record_from_model(conv, [msg])
    assert record.conversation_id == "key-1"
    assert record.messages[0].content == "hi"
    assert record.agent_entrypoint == "triage"
