"""User input resolution for agent runs."""

from __future__ import annotations

from typing import Any

from app.api.v1.chat.schemas import AgentChatRequest
from app.api.v1.shared.attachments import InputAttachment
from app.domain.ai.ports import AgentInput
from app.domain.conversations import ConversationAttachment
from app.domain.input_attachments import InputAttachmentRef
from app.services.agents.context import ConversationActorContext
from app.services.agents.input_attachments import InputAttachmentService


class UserInputResolver:
    """Resolve user message + attachments into agent input payloads."""

    def __init__(self, input_attachment_service: InputAttachmentService) -> None:
        self._input_attachment_service = input_attachment_service

    async def resolve(
        self,
        *,
        request: AgentChatRequest,
        actor: ConversationActorContext,
        conversation_id: str,
        agent_key: str,
    ) -> tuple[AgentInput, list[ConversationAttachment]]:
        attachments = self._coerce_input_attachments(getattr(request, "attachments", None))
        resolution = await self._input_attachment_service.resolve(
            attachments,
            actor=actor,
            conversation_id=conversation_id,
            agent_key=agent_key,
        )
        if not resolution.input_items:
            return request.message, resolution.attachments

        content: list[dict[str, Any]] = [
            {"type": "input_text", "text": request.message},
            *resolution.input_items,
        ]
        return [{"role": "user", "content": content}], resolution.attachments

    @staticmethod
    def _coerce_input_attachments(
        attachments: list[InputAttachment] | None,
    ) -> list[InputAttachmentRef] | None:
        if not attachments:
            return None
        return [
            InputAttachmentRef(object_id=att.object_id, kind=getattr(att, "kind", None))
            for att in attachments
        ]
