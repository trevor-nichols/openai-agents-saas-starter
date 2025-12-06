"""Helpers for persisting image_generation tool outputs."""

from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass

from app.core.settings import get_settings
from app.domain.conversations import ConversationAttachment
from app.services.storage.service import StorageService


@dataclass(slots=True)
class IngestedImage:
    attachment: ConversationAttachment
    storage_object_id: uuid.UUID
    size_bytes: int
    mime_type: str | None


def _coerce_conversation_uuid(conversation_id: str | None) -> uuid.UUID | None:
    if not conversation_id:
        return None
    try:
        return uuid.UUID(conversation_id)
    except (TypeError, ValueError):
        return uuid.uuid5(uuid.NAMESPACE_URL, f"api-service:conversation:{conversation_id}")


def _infer_mime(fmt: str) -> str:
    mapping = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "webp": "image/webp",
    }
    return mapping.get(fmt.lower(), "application/octet-stream")


async def ingest_image_output(
    *,
    image_b64: str,
    tenant_id: str,
    user_id: str | None,
    conversation_id: str | None,
    agent_key: str | None,
    tool_call_id: str | None,
    response_id: str | None,
    image_format: str | None,
    quality: str | None,
    background: str | None,
    storage_service: StorageService,
) -> IngestedImage:
    """Decode and persist an image returned by the image_generation tool."""

    settings = get_settings()
    raw_bytes = base64.b64decode(image_b64)
    size_bytes = len(raw_bytes)
    if size_bytes > settings.image_output_max_mb * 1024 * 1024:
        raise ValueError("Image exceeds configured size limit")

    fmt = (image_format or settings.image_default_format).lower()
    if fmt not in settings.image_allowed_formats:
        raise ValueError(f"Image format '{fmt}' is not allowed")

    mime = _infer_mime(fmt)
    file_name = f"image-{tool_call_id or response_id or uuid.uuid4().hex}.{fmt}"

    storage_obj = await storage_service.put_object(
        tenant_id=uuid.UUID(tenant_id),
        user_id=uuid.UUID(user_id) if user_id else None,
        data=raw_bytes,
        filename=file_name,
        mime_type=mime,
        agent_key=agent_key,
        conversation_id=_coerce_conversation_uuid(conversation_id),
        metadata={
            "tool_call_id": tool_call_id,
            "response_id": response_id,
            "format": fmt,
            "quality": quality,
            "background": background,
            "size_bytes": size_bytes,
        },
    )

    if storage_obj.id is None:
        raise RuntimeError("Storage provider returned object without id")

    attachment = ConversationAttachment(
        object_id=str(storage_obj.id),
        filename=file_name,
        mime_type=mime,
        size_bytes=size_bytes,
        tool_call_id=tool_call_id,
    )

    return IngestedImage(
        attachment=attachment,
        storage_object_id=storage_obj.id,
        size_bytes=size_bytes,
        mime_type=mime,
    )
