"""Shared schemas for attachment-based inputs."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class InputAttachment(BaseModel):
    """Reference to a stored object that should be passed to an agent as input."""

    object_id: uuid.UUID = Field(description="Storage object identifier")
    kind: Literal["image", "file"] | None = Field(
        default=None,
        description="Optional override for how the object should be sent to the model.",
    )


__all__ = ["InputAttachment"]
