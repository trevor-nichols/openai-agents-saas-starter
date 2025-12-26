"""Schemas for agent catalog endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentToolingFlags(BaseModel):
    """Stable capability flags for UI gating."""

    supports_code_interpreter: bool = Field(
        default=False, description="Whether the agent can use code_interpreter."
    )
    supports_file_search: bool = Field(
        default=False, description="Whether the agent can use file_search."
    )
    supports_image_generation: bool = Field(
        default=False, description="Whether the agent can use image_generation."
    )
    supports_web_search: bool = Field(
        default=False, description="Whether the agent can use web_search."
    )


class AgentSummary(BaseModel):
    """Lightweight representation of an available agent."""

    name: str = Field(description="Agent identifier.")
    status: Literal["active", "inactive", "error"] = Field(
        description="Health status of the agent.",
    )
    output_schema: dict[str, object] | None = Field(
        default=None,
        description="JSON Schema for the agent structured output, if declared.",
    )
    display_name: str | None = Field(
        default=None,
        description="Human-friendly display name for the agent.",
    )
    description: str | None = Field(
        default=None,
        description="Short human-readable description.",
    )
    model: str | None = Field(
        default=None,
        description="Model configured for this agent.",
    )
    tooling: AgentToolingFlags = Field(
        default_factory=AgentToolingFlags,
        description="Tooling capability flags for UI gating.",
    )
    last_seen_at: str | None = Field(
        default=None,
        description="Last time the agent was observed handling a request.",
    )


class AgentStatus(BaseModel):
    """Detailed information about a specific agent."""

    name: str = Field(description="Agent identifier.")
    status: Literal["active", "inactive", "error"] = Field(
        description="Operational status.",
    )
    output_schema: dict[str, object] | None = Field(
        default=None, description="JSON Schema for the agent structured output, if declared."
    )
    last_used: str | None = Field(
        default=None,
        description="Last time the agent was invoked.",
    )
    total_conversations: int = Field(
        default=0,
        description="Total number of conversations handled.",
    )
    tooling: AgentToolingFlags = Field(
        default_factory=AgentToolingFlags,
        description="Tooling capability flags for UI gating.",
    )


class AgentListResponse(BaseModel):
    """Paginated list of available agents."""

    items: list[AgentSummary]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page.",
    )
    total: int = Field(
        description="Total number of agents matching the current filter.",
    )
