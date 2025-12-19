"""Attachment ingestion and presigning helpers."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.domain.assets import AssetSourceTool, AssetType
from app.domain.conversations import ConversationAttachment, ConversationMessage
from app.services.agents.attachment_utils import coerce_conversation_uuid
from app.services.agents.container_file_ingestor import (
    ContainerFileCitationRef,
    ingest_container_file_citation,
)
from app.services.agents.image_ingestor import ingest_image_output
from app.services.assets.service import AssetService
from app.services.containers.files_gateway import ContainerFilesGateway
from app.services.storage.service import StorageService

logger = logging.getLogger(__name__)


class AttachmentService:
    """Handles persistence and presentation of tool-produced attachments."""

    def __init__(
        self,
        storage_resolver: Callable[[], StorageService],
        *,
        container_files_gateway_resolver: Callable[[], ContainerFilesGateway] | None = None,
        asset_service_resolver: Callable[[], AssetService] | None = None,
    ) -> None:
        self._storage_resolver = storage_resolver
        self._container_files_gateway_resolver = container_files_gateway_resolver
        self._asset_service_resolver = asset_service_resolver

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
                # Ignore partial frames; only persist finals so the conversation
                # history stores the finished asset once per tool call.
                status = (candidate.get("status") or "").lower()
                partial_idx = candidate.get("partial_image_index")
                if status == "partial_image" or partial_idx is not None:
                    continue

                if seen_tool_calls is not None and tool_call_id and tool_call_id in seen_tool_calls:
                    continue

                image_b64 = candidate.get("result") or candidate.get("b64_json")
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

                    await self._record_asset(
                        asset_type="image",
                        source_tool="image_generation",
                        tenant_id=uuid.UUID(actor.tenant_id),
                        storage_object_id=ingested.storage_object_id,
                        conversation_id=conversation_id,
                        tool_call_id=tool_call_id,
                        response_id=response_id,
                        metadata={
                            "format": image_format,
                            "quality": quality,
                            "background": background,
                        },
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

    async def ingest_container_file_citations(
        self,
        tool_outputs: list[Mapping[str, Any]] | None,
        *,
        actor,
        conversation_id: str,
        agent_key: str,
        response_id: str | None,
        seen_citations: set[str] | None = None,
    ) -> list[ConversationAttachment]:
        if not tool_outputs:
            return []
        if self._container_files_gateway_resolver is None:
            return []

        storage = self._storage_resolver()
        gateway = self._container_files_gateway_resolver()
        attachments: list[ConversationAttachment] = []
        dedupe = seen_citations if seen_citations is not None else set()

        for output in tool_outputs:
            if not isinstance(output, Mapping):
                continue
            for citation in _iter_container_file_citations(output):
                container_id = citation.get("container_id")
                file_id = citation.get("file_id")
                if not isinstance(container_id, str) or not isinstance(file_id, str):
                    continue
                dedupe_key = f"{container_id}:{file_id}"
                if dedupe_key in dedupe:
                    continue

                filename = citation.get("filename")
                try:
                    ingested = await ingest_container_file_citation(
                        tenant_id=actor.tenant_id,
                        user_id=getattr(actor, "user_id", None),
                        conversation_id=conversation_id,
                        agent_key=agent_key,
                        tool_call_id=None,
                        response_id=response_id,
                        citation=ContainerFileCitationRef(
                            container_id=container_id,
                            file_id=file_id,
                            filename=str(filename) if isinstance(filename, str) else None,
                        ),
                        gateway=gateway,
                        storage_service=storage,
                    )
                    asset_type = _infer_asset_type(ingested.mime_type)
                    await self._record_asset(
                        asset_type=asset_type,
                        source_tool="code_interpreter",
                        tenant_id=uuid.UUID(actor.tenant_id),
                        storage_object_id=ingested.storage_object_id,
                        conversation_id=conversation_id,
                        tool_call_id=None,
                        response_id=response_id,
                        container_id=container_id,
                        openai_file_id=file_id,
                        metadata={
                            "filename": ingested.attachment.filename,
                            "size_bytes": ingested.size_bytes,
                        },
                    )
                    presigned, _ = await storage.get_presigned_download(
                        tenant_id=uuid.UUID(actor.tenant_id),
                        object_id=ingested.storage_object_id,
                    )
                    ingested.attachment.presigned_url = presigned.url
                    dedupe.add(dedupe_key)
                    attachments.append(ingested.attachment)
                except Exception as exc:  # pragma: no cover
                    logger.warning(
                        "container_file.ingest_failed",
                        extra={
                            "tenant_id": actor.tenant_id,
                            "conversation_id": conversation_id,
                            "agent_key": agent_key,
                            "container_id": container_id,
                            "file_id": file_id,
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

    async def _record_asset(
        self,
        *,
        asset_type: AssetType,
        source_tool: AssetSourceTool | None,
        tenant_id: uuid.UUID,
        storage_object_id: uuid.UUID,
        conversation_id: str | None,
        tool_call_id: str | None,
        response_id: str | None,
        container_id: str | None = None,
        openai_file_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if self._asset_service_resolver is None:
            return
        try:
            service = self._asset_service_resolver()
        except Exception:
            logger.warning(
                "asset.service_unavailable",
                extra={"tenant_id": str(tenant_id)},
            )
            return
        try:
            await service.create_asset(
                tenant_id=tenant_id,
                storage_object_id=storage_object_id,
                asset_type=asset_type,
                source_tool=source_tool,
                conversation_id=coerce_conversation_uuid(conversation_id),
                message_id=None,
                tool_call_id=tool_call_id,
                response_id=response_id,
                container_id=container_id,
                openai_file_id=openai_file_id,
                metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "asset.record_failed",
                extra={
                    "tenant_id": str(tenant_id),
                    "storage_object_id": str(storage_object_id),
                    "asset_type": asset_type,
                    "source_tool": source_tool,
                },
                exc_info=exc,
            )


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

    # Tool-call item wrappers from SDK sessions
    raw_item = candidate.get("raw_item")
    if isinstance(raw_item, Mapping):
        yield from _iter_image_generation_calls(raw_item)


def _iter_container_file_citations(candidate: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    """Yield any container_file_citation mappings contained in a payload."""

    if candidate.get("type") == "container_file_citation":
        yield candidate

    annotations = candidate.get("annotations")
    if isinstance(annotations, list):
        for ann in annotations:
            if isinstance(ann, Mapping) and ann.get("type") == "container_file_citation":
                yield ann

    # Tool-call wrapper (code_interpreter_call includes annotations)
    ci = candidate.get("code_interpreter_call")
    if isinstance(ci, Mapping):
        yield from _iter_container_file_citations(ci)

    # Nested message content parts (Responses output items)
    content = candidate.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, Mapping):
                yield from _iter_container_file_citations(part)

    # Nested outputs list (e.g., response.completed payload)
    outputs = candidate.get("output") or candidate.get("outputs")
    if isinstance(outputs, list):
        for item in outputs:
            if isinstance(item, Mapping):
                yield from _iter_container_file_citations(item)

    raw_item = candidate.get("raw_item")
    if isinstance(raw_item, Mapping):
        yield from _iter_container_file_citations(raw_item)


def _infer_asset_type(mime_type: str | None) -> AssetType:
    if mime_type and mime_type.startswith("image/"):
        return "image"
    return "file"
