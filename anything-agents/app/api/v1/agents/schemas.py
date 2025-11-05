"""Schemas for agent catalog endpoints."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentSummary(BaseModel):
    """Lightweight representation of an available agent."""

    name: str = Field(description="Agent identifier.")
    status: Literal["active", "inactive", "error"] = Field(
        description="Health status of the agent.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Short human-readable description.",
    )


class AgentStatus(BaseModel):
    """Detailed information about a specific agent."""

    name: str = Field(description="Agent identifier.")
    status: Literal["active", "inactive", "error"] = Field(
        description="Operational status.",
    )
    last_used: Optional[str] = Field(
        default=None,
        description="Last time the agent was invoked.",
    )
    total_conversations: int = Field(
        default=0,
        description="Total number of conversations handled.",
    )
