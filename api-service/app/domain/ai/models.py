"""Provider-neutral value objects for AI agent orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(slots=True)
class AgentDescriptor:
    """Metadata describing an agent entry point exposed to the API layer."""

    key: str
    display_name: str
    description: str
    model: str
    capabilities: tuple[str, ...] = ()
    status: Literal["active", "inactive", "error"] = "active"


@dataclass(slots=True)
class AgentRunUsage:
    """Minimal usage snapshot propagated to billing/analytics layers."""

    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(slots=True)
class AgentRunResult:
    """Normalized payload returned by provider runtimes."""

    final_output: str
    response_id: str | None = None
    usage: AgentRunUsage | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(slots=True)
class AgentStreamEvent:
    """Represents a chunk of streamed assistant output."""

    content_delta: str
    is_terminal: bool = False


__all__ = [
    "AgentDescriptor",
    "AgentRunResult",
    "AgentRunUsage",
    "AgentStreamEvent",
]
