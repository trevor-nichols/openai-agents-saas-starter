"""Pure mappers between ORM rows and domain objects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast

from app.domain.conversations import (
    ConversationAttachment,
    ConversationEvent,
    ConversationMessage,
    ConversationRecord,
)
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
    AgentRunEvent,
)

MessageRole = Literal["user", "assistant", "system"]
_MESSAGE_ROLES: tuple[str, ...] = ("user", "assistant", "system")


def coerce_role(value: str) -> MessageRole:
    if value not in _MESSAGE_ROLES:
        raise ValueError(f"Unsupported conversation role '{value}'")
    return cast(MessageRole, value)


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def extract_message_content(payload: dict[str, object] | str | None) -> str:
    if isinstance(payload, dict):
        if "text" in payload:
            return str(payload["text"])
        return str(payload)
    if isinstance(payload, str):
        return payload
    return ""


def extract_attachments(payload: list[dict[str, object]] | None) -> list[ConversationAttachment]:
    if not payload:
        return []
    attachments: list[ConversationAttachment] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        mime = item.get("mime_type")
        size_val = item.get("size_bytes")
        attachments.append(
            ConversationAttachment(
                object_id=str(item.get("object_id", "")),
                filename=str(item.get("filename", "")),
                mime_type=str(mime) if isinstance(mime, str) else None,
                size_bytes=int(size_val) if isinstance(size_val, int) else None,
                presigned_url=None,
                tool_call_id=str(item.get("tool_call_id")) if item.get("tool_call_id") else None,
            )
        )
    return attachments


def serialize_attachments(attachments: list[ConversationAttachment]) -> list[dict[str, object]]:
    return [
        {
            "object_id": item.object_id,
            "filename": item.filename,
            "mime_type": item.mime_type,
            "size_bytes": item.size_bytes,
            "tool_call_id": item.tool_call_id,
        }
        for item in attachments
    ]


def message_from_row(row: AgentMessage) -> ConversationMessage:
    return ConversationMessage(
        role=coerce_role(row.role),
        content=extract_message_content(row.content),
        attachments=extract_attachments(row.attachments),
        timestamp=row.created_at,
    )


def record_from_model(
    conversation: AgentConversation, messages: list[AgentMessage]
) -> ConversationRecord:
    message_objs = [message_from_row(item) for item in messages]
    return ConversationRecord(
        conversation_id=conversation.conversation_key,
        messages=message_objs,
        display_name=conversation.display_name,
        agent_entrypoint=conversation.agent_entrypoint,
        active_agent=conversation.active_agent,
        topic_hint=conversation.topic_hint,
        status=conversation.status,
        title_generated_at=conversation.title_generated_at,
        created_at_value=conversation.created_at,
        updated_at_value=conversation.updated_at,
    )


def run_event_from_row(row: AgentRunEvent) -> ConversationEvent:
    return ConversationEvent(
        run_item_type=row.run_item_type,
        run_item_name=row.run_item_name,
        role=coerce_role(row.role) if row.role else None,
        agent=row.agent,
        tool_call_id=row.tool_call_id,
        tool_name=row.tool_name,
        model=row.model,
        content_text=row.content_text,
        reasoning_text=row.reasoning_text,
        call_arguments=row.call_arguments or None,
        call_output=row.call_output or None,
        attachments=extract_attachments(row.attachments),
        response_id=row.response_id,
        sequence_no=row.sequence_no,
        workflow_run_id=row.workflow_run_id,
        timestamp=row.created_at,
    )


def coerce_mapping(value: object | None) -> dict[str, object] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"value": value}


__all__ = [
    "MessageRole",
    "coerce_role",
    "to_utc",
    "extract_message_content",
    "extract_attachments",
    "serialize_attachments",
    "message_from_row",
    "record_from_model",
    "run_event_from_row",
    "coerce_mapping",
]
