"""Domain model for user-provided input attachments."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

InputAttachmentKind = Literal["image", "file"]


class InputAttachmentNotFoundError(RuntimeError):
    """Raised when a referenced input attachment cannot be resolved."""


@dataclass(slots=True)
class InputAttachmentRef:
    object_id: uuid.UUID
    kind: InputAttachmentKind | None = None


__all__ = ["InputAttachmentKind", "InputAttachmentNotFoundError", "InputAttachmentRef"]
