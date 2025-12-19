"""Pydantic schemas for tool catalog endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolCatalogResponse(BaseModel):
    """Stable, typed shape for the tool catalog response."""

    total_tools: int = Field(ge=0)
    tool_names: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    per_agent: dict[str, list[str]] = Field(default_factory=dict)


__all__ = ["ToolCatalogResponse"]

