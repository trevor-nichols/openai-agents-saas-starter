# File: app/schemas/agents.py
# Purpose: Agent interaction schemas for anything-agents
# Dependencies: pydantic
# Used by: Agent routers for request/response validation

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

# =============================================================================
# AGENT REQUEST/RESPONSE SCHEMAS
# =============================================================================

class ChatMessage(BaseModel):
    """Individual chat message schema."""
    
    role: Literal["user", "assistant", "system"] = Field(description="Message role")
    content: str = Field(description="Message content")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")

class AgentChatRequest(BaseModel):
    """Agent chat request schema."""
    
    message: str = Field(description="User message to the agent")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    agent_type: Optional[str] = Field(default="triage", description="Specific agent to use")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class AgentChatResponse(BaseModel):
    """Agent chat response schema."""
    
    response: str = Field(description="Agent response")
    conversation_id: str = Field(description="Conversation ID")
    agent_used: str = Field(description="Which agent handled the request")
    handoff_occurred: bool = Field(default=False, description="Whether a handoff occurred")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional response metadata")

class StreamingChatResponse(BaseModel):
    """Streaming chat response chunk schema."""
    
    chunk: str = Field(description="Response chunk")
    conversation_id: str = Field(description="Conversation ID")
    is_complete: bool = Field(default=False, description="Whether this is the final chunk")
    agent_used: Optional[str] = Field(default=None, description="Which agent is responding")

# =============================================================================
# CONVERSATION MANAGEMENT SCHEMAS
# =============================================================================

class ConversationHistory(BaseModel):
    """Conversation history schema."""
    
    conversation_id: str = Field(description="Conversation ID")
    messages: List[ChatMessage] = Field(description="List of messages in conversation")
    created_at: str = Field(description="Conversation creation timestamp")
    updated_at: str = Field(description="Last update timestamp")
    agent_context: Optional[Dict[str, Any]] = Field(default=None, description="Agent-specific context")

class ConversationSummary(BaseModel):
    """Conversation summary schema."""
    
    conversation_id: str = Field(description="Conversation ID")
    message_count: int = Field(description="Number of messages")
    last_message: str = Field(description="Last message preview")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")

# =============================================================================
# AGENT CONFIGURATION SCHEMAS
# =============================================================================

class AgentConfig(BaseModel):
    """Agent configuration schema."""
    
    name: str = Field(description="Agent name")
    instructions: str = Field(description="Agent instructions/system prompt")
    model: str = Field(default="gpt-4.1-2025-04-14", description="Model to use")
    tools: Optional[List[str]] = Field(default=None, description="Available tools")
    handoff_agents: Optional[List[str]] = Field(default=None, description="Agents this can handoff to")
    is_active: bool = Field(default=True, description="Whether agent is active")

class AgentStatus(BaseModel):
    """Agent status schema."""
    
    name: str = Field(description="Agent name")
    status: Literal["active", "inactive", "error"] = Field(description="Agent status")
    last_used: Optional[str] = Field(default=None, description="Last usage timestamp")
    total_conversations: int = Field(default=0, description="Total conversations handled") 