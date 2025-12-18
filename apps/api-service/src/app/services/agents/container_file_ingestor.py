"""Helpers for persisting code_interpreter container file outputs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.domain.conversations import ConversationAttachment
from app.services.agents.attachment_utils import coerce_conversation_uuid
from app.services.containers.files_gateway import ContainerFileContent, ContainerFilesGateway
from app.services.storage.service import StorageService
from app.utils.filenames import sanitize_download_filename


@dataclass(slots=True)
class ContainerFileCitationRef:
    container_id: str
    file_id: str
    filename: str | None = None


@dataclass(slots=True)
class IngestedContainerFile:
    attachment: ConversationAttachment
    storage_object_id: uuid.UUID
    size_bytes: int
    mime_type: str | None


_MIME_BY_EXT: dict[str, str] = {
    # Code Interpreter supported formats (see
    # docs/integrations/openai-agents-sdk/tools/code_interpreter/code-interpreter-and-containers.md)
    "c": "text/x-c",
    "cs": "text/x-csharp",
    "cpp": "text/x-c++",
    "csv": "text/csv",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "html": "text/html",
    "java": "text/x-java",
    "json": "application/json",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "php": "text/x-php",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "py": "text/x-python",
    "rb": "text/x-ruby",
    "tex": "text/x-tex",
    "txt": "text/plain",
    "css": "text/css",
    "js": "text/javascript",
    "sh": "application/x-sh",
    "ts": "application/typescript",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "gif": "image/gif",
    "pkl": "application/octet-stream",
    "png": "image/png",
    "tar": "application/x-tar",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xml": "application/xml",
    "zip": "application/zip",
    # Fallback formats we explicitly want to keep compatible with our storage allowlist.
    "webp": "image/webp",
}


def _infer_mime(filename: str) -> str:
    token = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _MIME_BY_EXT.get(token, "application/octet-stream")


async def ingest_container_file_citation(
    *,
    tenant_id: str,
    user_id: str | None,
    conversation_id: str | None,
    agent_key: str | None,
    tool_call_id: str | None,
    response_id: str | None,
    citation: ContainerFileCitationRef,
    gateway: ContainerFilesGateway,
    storage_service: StorageService,
) -> IngestedContainerFile:
    """Download a container file from OpenAI and persist it to tenant storage."""

    content: ContainerFileContent = await gateway.download_file_content(
        tenant_id=uuid.UUID(tenant_id),
        container_id=citation.container_id,
        file_id=citation.file_id,
    )
    size_bytes = len(content.data)

    preferred_filename = sanitize_download_filename(citation.filename)
    remote_filename = sanitize_download_filename(content.filename)
    filename = preferred_filename or remote_filename or f"{citation.file_id}.bin"

    mime = _infer_mime(filename)

    storage_obj = await storage_service.put_object(
        tenant_id=uuid.UUID(tenant_id),
        user_id=uuid.UUID(user_id) if user_id else None,
        data=content.data,
        filename=filename,
        mime_type=mime,
        agent_key=agent_key,
        conversation_id=coerce_conversation_uuid(conversation_id),
        metadata={
            "tool_call_id": tool_call_id,
            "response_id": response_id,
            "container_id": citation.container_id,
            "file_id": citation.file_id,
            "filename": filename,
            "size_bytes": size_bytes,
        },
    )

    if storage_obj.id is None:
        raise RuntimeError("Storage provider returned object without id")

    attachment = ConversationAttachment(
        object_id=str(storage_obj.id),
        filename=filename,
        mime_type=mime,
        size_bytes=size_bytes,
        tool_call_id=tool_call_id,
    )

    return IngestedContainerFile(
        attachment=attachment,
        storage_object_id=storage_obj.id,
        size_bytes=size_bytes,
        mime_type=mime,
    )


__all__ = [
    "ContainerFileCitationRef",
    "IngestedContainerFile",
    "ingest_container_file_citation",
]
