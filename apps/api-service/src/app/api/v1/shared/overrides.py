"""Shared request schemas for per-agent overrides."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class VectorStoreOverride(BaseModel):
    """Per-agent vector store override payload."""

    vector_store_id: str | None = Field(
        default=None,
        description="Single vector store id (DB UUID or OpenAI vector store id).",
    )
    vector_store_ids: list[str] | None = Field(
        default=None,
        description="List of vector store ids (DB UUID or OpenAI vector store ids).",
    )

    @model_validator(mode="after")
    def _validate_one_of(self) -> VectorStoreOverride:
        has_single = bool(self.vector_store_id)
        has_many = bool(self.vector_store_ids)
        if has_single == has_many:
            raise ValueError(
                "Provide exactly one of vector_store_id or vector_store_ids."
            )
        return self

    def to_payload(self) -> dict[str, Any]:
        if self.vector_store_id:
            return {"vector_store_id": self.vector_store_id}
        return {"vector_store_ids": list(self.vector_store_ids or [])}


VectorStoreOverrides = dict[str, VectorStoreOverride]

__all__ = ["VectorStoreOverride", "VectorStoreOverrides"]
