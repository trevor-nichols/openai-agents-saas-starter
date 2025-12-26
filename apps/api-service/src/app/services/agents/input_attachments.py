"""User-provided input attachment resolution for agent runs."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from app.core.settings import Settings, get_settings
from app.domain.conversations import ConversationAttachment
from app.domain.input_attachments import (
    InputAttachmentKind,
    InputAttachmentNotFoundError,
    InputAttachmentRef,
)
from app.services.agents.attachment_utils import coerce_conversation_uuid
from app.services.assets.service import AssetService
from app.services.storage.service import StorageService

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class InputAttachmentResolution:
    input_items: list[dict[str, Any]]
    attachments: list[ConversationAttachment]


class InputAttachmentService:
    """Validate and translate stored objects into SDK input items."""

    def __init__(
        self,
        storage_resolver: Callable[[], StorageService],
        *,
        asset_service_resolver: Callable[[], AssetService] | None = None,
        settings_factory: Callable[[], Settings] = get_settings,
    ) -> None:
        self._storage_resolver = storage_resolver
        self._asset_service_resolver = asset_service_resolver
        self._settings_factory = settings_factory

    async def resolve(
        self,
        attachments: Iterable[InputAttachmentRef] | None,
        *,
        actor,
        conversation_id: str,
        agent_key: str,
    ) -> InputAttachmentResolution:
        if not attachments:
            return InputAttachmentResolution(input_items=[], attachments=[])

        settings = self._settings_factory()
        storage = self._storage_resolver()
        asset_service = self._asset_service_resolver() if self._asset_service_resolver else None

        input_items: list[dict[str, Any]] = []
        message_attachments: list[ConversationAttachment] = []
        seen: set[uuid.UUID] = set()

        for attachment in attachments:
            object_id = uuid.UUID(str(attachment.object_id))
            if object_id in seen:
                continue
            seen.add(object_id)

            try:
                presigned, obj = await storage.get_presigned_download(
                    tenant_id=uuid.UUID(actor.tenant_id),
                    object_id=object_id,
                )
            except FileNotFoundError as exc:
                raise InputAttachmentNotFoundError("Attachment not found") from exc
            if obj is None:
                raise ValueError("Attachment not found")
            mime_type = getattr(obj, "mime_type", None)
            if not mime_type:
                raise ValueError("Attachment mime_type is required")

            _ensure_allowed_mime(settings, mime_type)

            kind = _resolve_kind(attachment.kind, mime_type)
            filename = getattr(obj, "filename", None) or f"{object_id}"
            size_bytes = getattr(obj, "size_bytes", None)

            if kind == "image":
                input_items.append(
                    {
                        "type": "input_image",
                        "image_url": presigned.url,
                        "detail": "auto",
                    }
                )
            else:
                input_items.append(
                    {
                        "type": "input_file",
                        "file_url": presigned.url,
                        "filename": filename,
                    }
                )

            message_attachments.append(
                ConversationAttachment(
                    object_id=str(object_id),
                    filename=filename,
                    mime_type=mime_type,
                    size_bytes=size_bytes,
                    presigned_url=presigned.url,
                    tool_call_id=None,
                )
            )

            if asset_service is not None:
                try:
                    await asset_service.create_asset(
                        tenant_id=uuid.UUID(actor.tenant_id),
                        storage_object_id=object_id,
                        asset_type="image" if kind == "image" else "file",
                        source_tool="user_upload",
                        conversation_id=coerce_conversation_uuid(conversation_id),
                        message_id=None,
                        tool_call_id=None,
                        response_id=None,
                        container_id=None,
                        openai_file_id=None,
                        metadata={
                            "filename": filename,
                            "mime_type": mime_type,
                            "size_bytes": size_bytes,
                        },
                    )
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning(
                        "asset.record_failed",
                        extra={
                            "tenant_id": str(actor.tenant_id),
                            "storage_object_id": str(object_id),
                            "asset_type": "image" if kind == "image" else "file",
                            "source_tool": "user_upload",
                        },
                        exc_info=exc,
                    )

        return InputAttachmentResolution(
            input_items=input_items,
            attachments=message_attachments,
        )


def _ensure_allowed_mime(settings: Settings, mime_type: str) -> None:
    allowed = getattr(settings, "storage_allowed_mime_types", None) or []
    if allowed and mime_type not in allowed:
        raise ValueError(f"Attachment mime_type '{mime_type}' is not allowed")


def _resolve_kind(requested: InputAttachmentKind | None, mime_type: str) -> InputAttachmentKind:
    is_image = mime_type.startswith("image/")
    if requested is None:
        return "image" if is_image else "file"
    if requested == "image" and not is_image:
        raise ValueError("Attachment kind 'image' requires an image/* mime_type")
    return requested


__all__ = ["InputAttachmentService", "InputAttachmentResolution"]
