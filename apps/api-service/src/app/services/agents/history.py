"""Conversation history orchestration helpers."""

from __future__ import annotations

from datetime import datetime

from app.api.v1.chat.schemas import MessageAttachment
from app.api.v1.conversations.schemas import ChatMessage, ConversationHistory, ConversationSummary
from app.services.agents.attachments import AttachmentService
from app.services.conversation_service import ConversationService, SearchResult


class ConversationHistoryService:
    """Wraps ConversationService with API-facing projections."""

    def __init__(
        self,
        conversation_service: ConversationService,
        attachment_service: AttachmentService,
    ) -> None:
        self._conversation_service = conversation_service
        self._attachments = attachment_service

    async def get_history(
        self, conversation_id: str, *, actor
    ) -> ConversationHistory:
        messages = await self._conversation_service.get_messages(
            conversation_id, tenant_id=actor.tenant_id
        )
        if not messages:
            raise ValueError(f"Conversation {conversation_id} not found")

        await self._attachments.presign_message_attachments(
            messages, tenant_id=actor.tenant_id
        )

        api_messages = [self._to_chat_message(msg) for msg in messages]
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=api_messages,
            created_at=messages[0].timestamp.isoformat(),
            updated_at=messages[-1].timestamp.isoformat(),
        )

    async def list_summaries(
        self,
        *,
        actor,
        limit: int,
        cursor: str | None,
        agent_entrypoint: str | None,
        updated_after: datetime | None,
    ) -> tuple[list[ConversationSummary], str | None]:
        page = await self._conversation_service.paginate_conversations(
            tenant_id=actor.tenant_id,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

        summaries: list[ConversationSummary] = []
        for record in page.items:
            if not record.messages:
                continue
            last_message = record.messages[-1]
            summaries.append(
                ConversationSummary(
                    conversation_id=record.conversation_id,
                    message_count=len(record.messages),
                    last_message=last_message.content[:160],
                    created_at=record.created_at.isoformat(),
                    updated_at=record.updated_at.isoformat(),
                )
            )

        return summaries, page.next_cursor

    async def search(
        self,
        *,
        actor,
        query: str,
        limit: int,
        cursor: str | None,
        agent_entrypoint: str | None,
    ) -> tuple[list[SearchResult], str | None]:
        page = await self._conversation_service.search(
            tenant_id=actor.tenant_id,
            query=query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )
        return page.items, page.next_cursor

    async def clear(self, conversation_id: str, *, actor) -> None:
        await self._conversation_service.clear_conversation(
            conversation_id, tenant_id=actor.tenant_id
        )

    @staticmethod
    def _to_chat_message(message) -> ChatMessage:
        return ChatMessage(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
            attachments=[
                MessageAttachment(
                    object_id=att.object_id,
                    filename=att.filename,
                    mime_type=att.mime_type,
                    size_bytes=att.size_bytes,
                    url=att.presigned_url,
                    tool_call_id=att.tool_call_id,
                )
                for att in message.attachments
            ],
        )


__all__ = ["ConversationHistoryService"]
