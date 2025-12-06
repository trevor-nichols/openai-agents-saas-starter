from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.api.v1.shared.streaming import (
    CodeInterpreterCall,
    ContainerFileCitation,
    FileCitation,
    FileSearchCall,
    ImageGenerationCall,
    MessageAttachment,
    StreamingEvent,
    ToolCallPayload,
    UrlCitation,
    WebSearchAction,
    WebSearchCall,
)


class AgentRunOptions(BaseModel):
    """Optional per-request runtime knobs forwarded to the Agents SDK."""

    max_turns: int | None = None
    previous_response_id: str | None = None
    # Name of the handoff filter (see app/agents/_shared/handoff_filters.py).
    handoff_input_filter: str | None = None
    # Convenience alias for common policies; maps to handoff_input_filter.
    handoff_context_policy: Literal["full", "fresh", "last_turn"] | None = None
    run_config: dict[str, Any] | None = None


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    agent_type: str | None = None
    share_location: bool | None = None
    location: LocationHint | None = None
    context: dict[str, Any] | None = None
    run_options: AgentRunOptions | None = None


class AgentChatResponse(BaseModel):
    conversation_id: str
    message: str | None = None
    response: str
    agent_used: str | None = None
    handoff_occurred: bool | None = None
    attachments: list[MessageAttachment] | None = None
    structured_output: Any | None = None
    metadata: dict[str, Any] | None = None


class LocationHint(BaseModel):
    city: str | None = None
    region: str | None = None
    country: str | None = None
    timezone: str | None = None


class StreamingChatEvent(StreamingEvent):
    model_config = ConfigDict(title="StreamingChatEvent")


__all__ = [
    "AgentChatRequest",
    "AgentChatResponse",
    "StreamingChatEvent",
    "ToolCallPayload",
    "UrlCitation",
    "ContainerFileCitation",
    "FileCitation",
    "MessageAttachment",
    "WebSearchAction",
    "WebSearchCall",
    "CodeInterpreterCall",
    "FileSearchCall",
    "ImageGenerationCall",
    "LocationHint",
    "AgentRunOptions",
]
