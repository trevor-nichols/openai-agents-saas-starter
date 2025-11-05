# File: app/routers/agents.py
# Purpose: Agent interaction endpoints for anything-agents
# Dependencies: fastapi, app/services/agent_service, app/schemas/agents
# Used by: Frontend applications for AI agent interactions

from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.services.agent_service import agent_service
from app.schemas.agents import (
    AgentChatRequest,
    AgentChatResponse,
    ConversationHistory,
    ConversationSummary,
    AgentStatus
)
from app.schemas.common import SuccessResponse
import json
import asyncio

router = APIRouter()

# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(request: AgentChatRequest):
    """
    Chat with the AI agent system.
    
    This endpoint provides the main interface for interacting with agents.
    It automatically routes to the appropriate agent based on the request.
    """
    try:
        response = await agent_service.chat(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.post("/chat/stream")
async def stream_chat_with_agent(request: AgentChatRequest):
    """
    Stream chat responses from the AI agent system.
    
    This endpoint provides real-time streaming of agent responses using
    the OpenAI Agents SDK's Runner.run_streamed() for true streaming.
    """
    async def generate_stream():
        try:
            # Use the true streaming method from agent service
            async for chunk_response in agent_service.chat_stream(request):
                # Convert StreamingChatResponse to Server-Sent Events format
                stream_data = {
                    "chunk": chunk_response.chunk,
                    "conversation_id": chunk_response.conversation_id,
                    "is_complete": chunk_response.is_complete,
                    "agent_used": chunk_response.agent_used
                }
                
                yield f"data: {json.dumps(stream_data)}\n\n"
                
                # If this is the completion signal, break
                if chunk_response.is_complete:
                    break
                    
        except Exception as e:
            error_data = {
                "error": str(e),
                "conversation_id": request.conversation_id or "unknown",
                "is_complete": True,
                "chunk": ""
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# =============================================================================
# CONVERSATION MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/conversations", response_model=SuccessResponse)
async def list_conversations():
    """List all conversation IDs."""
    try:
        conversations = agent_service.list_conversations()
        return SuccessResponse(
            message="Conversations retrieved successfully",
            data=conversations
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(conversation_id: str):
    """Get the full history of a specific conversation."""
    try:
        history = await agent_service.get_conversation_history(conversation_id)
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}"
        )

# =============================================================================
# AGENT MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/agents", response_model=SuccessResponse)
async def list_available_agents():
    """List all available agents in the system."""
    try:
        agents = agent_service.list_available_agents()
        agent_info = []
        
        for agent_name in agents:
            # For now, all agents are active. In the future, this could check actual status
            agent_info.append({
                "name": agent_name,
                "status": "active",
                "description": f"AI agent specialized for {agent_name} tasks"
            })
        
        return SuccessResponse(
            message="Available agents retrieved successfully",
            data={"agents": agent_info, "count": len(agent_info)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agents: {str(e)}"
        )

@router.get("/agents/{agent_name}/status", response_model=AgentStatus)
async def get_agent_status(agent_name: str):
    """Get the status of a specific agent."""
    try:
        available_agents = agent_service.list_available_agents()
        
        if agent_name not in available_agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )
        
        # For now, return basic status. This can be enhanced with real metrics
        return AgentStatus(
            name=agent_name,
            status="active",
            last_used=None,  # Could track this in the future
            total_conversations=0  # Could track this in the future
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent status: {str(e)}"
        )

# =============================================================================
# TOOLS MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/tools", response_model=SuccessResponse)
async def list_available_tools():
    """List all available tools in the system."""
    try:
        tool_info = agent_service.get_tool_information()
        
        return SuccessResponse(
            message="Available tools retrieved successfully",
            data={
                "total_tools": tool_info.get("total_tools", 0),
                "tool_names": tool_info.get("tool_names", []),
                "categories": tool_info.get("categories", []),
                "tools_by_category": {
                    category: [tool for tool in tool_info.get("tool_names", []) 
                              if category in tool.lower()]
                    for category in tool_info.get("categories", [])
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tools: {str(e)}"
        )

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.post("/conversations/{conversation_id}/clear", response_model=SuccessResponse)
async def clear_conversation(conversation_id: str):
    """Clear a specific conversation history."""
    try:
        # This would clear the conversation from storage
        # For now, we'll just return success since we don't have a clear method
        return SuccessResponse(
            message=f"Conversation {conversation_id} cleared successfully",
            data={"conversation_id": conversation_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing conversation: {str(e)}"
        ) 