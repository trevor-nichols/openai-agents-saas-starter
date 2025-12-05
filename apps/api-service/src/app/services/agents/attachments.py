"""Attachment ingestion and presigning helpers."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.domain.conversations import ConversationAttachment, ConversationMessage
from app.services.agents.image_ingestor import ingest_image_output
from app.services.storage.service import StorageService

logger = logging.getLogger(__name__)


class AttachmentService:
    """Handles persistence and presentation of tool-produced attachments."""

    def __init__(self, storage_resolver: Callable[[], StorageService]) -> None:
        self._storage_resolver = storage_resolver

    async def ingest_image_outputs(
        self,
        tool_outputs: list[Mapping[str, Any]] | None,
        *,
        actor,
        conversation_id: str,
        agent_key: str,
        response_id: str | None,
        seen_tool_calls: set[str] | None = None,
    ) -> list[ConversationAttachment]:
        if not tool_outputs:
            return []

        storage = self._storage_resolver()
        attachments: list[ConversationAttachment] = []

        for output in tool_outputs:
            if not isinstance(output, Mapping):
                continue

            for candidate in _iter_image_generation_calls(output):
                tool_call_id = candidate.get("id") or candidate.get("tool_call_id")
                if seen_tool_calls is not None and tool_call_id and tool_call_id in seen_tool_calls:
                    continue
                image_b64 = (
                    candidate.get("result")
                    or candidate.get("b64_json")
                    or candidate.get("partial_image_b64")
                )
                if not image_b64:
                    continue
                quality = candidate.get("quality")
                background = candidate.get("background")
                image_format = candidate.get("format") or candidate.get("output_format")

                try:
                    ingested = await ingest_image_output(
                        image_b64=image_b64,
                        tenant_id=actor.tenant_id,
                        user_id=actor.user_id,
                        conversation_id=conversation_id,
                        agent_key=agent_key,
                        tool_call_id=tool_call_id,
                        response_id=response_id,
                        image_format=image_format,
                        quality=quality,
                        background=background,
                        storage_service=storage,
                    )

                    presigned, _ = await storage.get_presigned_download(
                        tenant_id=uuid.UUID(actor.tenant_id),
                        object_id=ingested.storage_object_id,
                    )
                    ingested.attachment.presigned_url = presigned.url
                    if seen_tool_calls is not None and tool_call_id:
                        seen_tool_calls.add(tool_call_id)
                    attachments.append(ingested.attachment)
                except Exception as exc:  # pragma: no cover
                    logger.warning(
                        "image.ingest_failed",
                        extra={
                            "tenant_id": actor.tenant_id,
                            "conversation_id": conversation_id,
                            "agent_key": agent_key,
                            "tool_call_id": tool_call_id,
                        },
                        exc_info=exc,
                    )
                    continue

        return attachments

    async def presign_message_attachments(
        self, messages: list[ConversationMessage], *, tenant_id: str
    ) -> None:
        if not any(msg.attachments for msg in messages):
            return

        storage = self._storage_resolver()
        for message in messages:
            for attachment in message.attachments:
                if attachment.presigned_url:
                    continue
                try:
                    presigned, _ = await storage.get_presigned_download(
                        tenant_id=uuid.UUID(tenant_id), object_id=uuid.UUID(attachment.object_id)
                    )
                    attachment.presigned_url = presigned.url
                except Exception:
                    logger.warning(
                        "attachment.presign_failed",
                        extra={"object_id": attachment.object_id, "tenant_id": tenant_id},
                    )

    @staticmethod
    def to_attachment_schema(attachment: ConversationAttachment) -> dict[str, Any]:
        return {
            "object_id": attachment.object_id,
            "filename": attachment.filename,
            "mime_type": attachment.mime_type,
            "size_bytes": attachment.size_bytes,
            "url": attachment.presigned_url,
            "tool_call_id": attachment.tool_call_id,
        }

    def to_attachment_payload(self, attachment: ConversationAttachment) -> dict[str, Any]:
        return self.to_attachment_schema(attachment)

    @staticmethod
    def attachment_metadata_note(attachments: list[ConversationAttachment]) -> dict[str, Any]:
        if not attachments:
            return {}
        return {"attachments": {"status": "stored", "count": len(attachments)}}


__all__ = ["AttachmentService"]


def _iter_image_generation_calls(candidate: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    """Yield any image_generation_call mappings contained in a payload or tool_call."""

    # Direct
    if candidate.get("type") == "image_generation_call":
        yield candidate

    # Tool-call wrapper
    ig = candidate.get("image_generation_call")
    if isinstance(ig, Mapping):
        yield ig

    # Nested outputs list (e.g., response.completed payload)
    outputs = candidate.get("output") or candidate.get("outputs")
    if isinstance(outputs, list):
        for item in outputs:
            if isinstance(item, Mapping) and item.get("type") == "image_generation_call":
                yield item
