"""Schemas for agent catalog endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


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
