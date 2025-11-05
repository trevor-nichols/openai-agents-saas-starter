# File: app/services/agent_service.py
# Purpose: Core agent service implementing extensible triage pattern
# Dependencies: agents (OpenAI SDK), app/core/config, app/schemas/agents, app/utils/tools
# Used by: Agent routers for handling chat interactions

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from agents import Agent, Runner, function_tool, trace
from openai.types.responses import ResponseTextDeltaEvent
from app.core.config import get_settings
from app.schemas.agents import (
    ChatMessage, 
    AgentChatRequest, 
    AgentChatResponse,
    ConversationHistory,
    StreamingChatResponse
)
from app.utils.tools import get_tool_registry, initialize_tools

# =============================================================================
# CONVERSATION STORAGE (In-memory for now, easily replaceable with Redis/DB)
# =============================================================================

class ConversationStore:
    """Simple in-memory conversation storage."""
    
    def __init__(self):
        self._conversations: Dict[str, List[ChatMessage]] = {}
    
    def get_conversation(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history."""
        return self._conversations.get(conversation_id, [])
    
    def add_message(self, conversation_id: str, message: ChatMessage):
        """Add message to conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append(message)
    
    def get_conversation_ids(self) -> List[str]:
        """Get all conversation IDs."""
        return list(self._conversations.keys())

# Global conversation store instance
conversation_store = ConversationStore()

# =============================================================================
# AGENT TOOLS (Functions that agents can use)
# =============================================================================

@function_tool
async def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@function_tool
async def search_conversations(query: str) -> str:
    """Search through conversation history for relevant information."""
    # Simple search implementation - can be enhanced with vector search
    conversations = conversation_store._conversations
    results = []
    
    for conv_id, messages in conversations.items():
        for msg in messages:
            if query.lower() in msg.content.lower():
                results.append(f"Found in {conv_id}: {msg.content[:100]}...")
                break
    
    return f"Found {len(results)} relevant conversations: " + "; ".join(results[:3])

# =============================================================================
# SPECIALIZED AGENTS (Easy to add more)
# =============================================================================

class AgentFactory:
    """Factory for creating and managing agents."""
    
    def __init__(self):
        self.settings = get_settings()
        self._agents: Dict[str, Agent] = {}
        self._tool_registry = None
        self._initialize_tools()
        self._initialize_agents()
    
    def _initialize_tools(self):
        """Initialize the tool registry with all available tools."""
        self._tool_registry = initialize_tools()
        
        # Register local tools
        self._tool_registry.register_tool(
            get_current_time,
            category="utility",
            metadata={"description": "Get current date and time"}
        )
        
        self._tool_registry.register_tool(
            search_conversations,
            category="conversation",
            metadata={"description": "Search conversation history"}
        )
    
    def _get_agent_tools(self, agent_type: str = "triage") -> List:
        """
        Get tools for a specific agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List: List of tools for the agent
        """
        if not self._tool_registry:
            return []
        
        # Get core tools (available to all agents)
        core_tools = self._tool_registry.get_core_tools()
        
        # Get specialized tools for this agent type
        specialized_tools = self._tool_registry.get_specialized_tools(agent_type)
        
        # Combine all tools
        all_tools = core_tools + specialized_tools
        
        return all_tools
    
    def _initialize_agents(self):
        """Initialize all available agents."""
        
        # Get tools for agents
        triage_tools = self._get_agent_tools("triage")
        code_tools = self._get_agent_tools("code_assistant")
        data_tools = self._get_agent_tools("data_analyst")
        
        # Main Triage Agent - this is your primary chatbot
        self._agents["triage"] = Agent(
            name="Triage Assistant",
            instructions="""
            You are a helpful AI assistant and the main point of contact for users.
            
            You can handle general questions, provide information, and help with various tasks.
            You have access to web search capabilities to find current information and answer
            questions that require up-to-date data.
            
            For now, you handle all requests directly, but you're designed to work with 
            specialized agents in the future. Always be helpful, friendly, and informative.
            
            When users ask about current events, recent information, or anything that might
            require real-time data, use the web search tool to provide accurate, up-to-date
            information.
            
            If a user asks about something very technical or specialized, acknowledge that
            you can help but mention that specialized agents may be added in the future
            for even better assistance.
            """,
            model="gpt-4.1-2025-04-14",
            tools=triage_tools
        )
        
        # Example specialized agents (inactive for now, but ready to activate)
        self._agents["code_assistant"] = Agent(
            name="Code Assistant",
            instructions="""
            You are a specialized coding assistant. You help with:
            - Code review and debugging
            - Architecture suggestions
            - Best practices
            - Framework-specific guidance
            
            You have access to web search to find the latest documentation,
            best practices, and solutions to coding problems.
            
            Always provide clear, well-commented code examples.
            """,
            model="gpt-4.1-2025-04-14",
            tools=code_tools
        )
        
        self._agents["data_analyst"] = Agent(
            name="Data Analyst",
            instructions="""
            You are a data analysis specialist. You help with:
            - Data interpretation
            - Statistical analysis
            - Visualization suggestions
            - Data cleaning strategies
            
            You have access to web search to find the latest data analysis
            techniques, tools, and best practices.
            
            Always explain your reasoning clearly.
            """,
            model="gpt-4.1-2025-04-14",
            tools=data_tools
        )
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all available agent names."""
        return list(self._agents.keys())
    
    def add_agent(self, name: str, agent: Agent):
        """Add a new agent (for future extensibility)."""
        self._agents[name] = agent
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about available tools."""
        if not self._tool_registry:
            return {}
        
        return {
            "total_tools": len(self._tool_registry.list_tool_names()),
            "tool_names": self._tool_registry.list_tool_names(),
            "categories": self._tool_registry.list_categories()
        }

# Global agent factory instance
agent_factory = AgentFactory()

# =============================================================================
# MAIN AGENT SERVICE
# =============================================================================

class AgentService:
    """Main service for handling agent interactions."""
    
    def __init__(self):
        self.factory = agent_factory
        self.store = conversation_store
    
    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        """
        Handle a chat request with the agent system.
        
        This method implements the extensible triage pattern:
        1. Start with the main triage agent
        2. Can easily be extended to route to specialized agents
        3. Maintains conversation context
        """
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = self.store.get_conversation(conversation_id)
        
        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        self.store.add_message(conversation_id, user_message)
        
        # Determine which agent to use (for now, always triage)
        agent_name = request.agent_type or "triage"
        agent = self.factory.get_agent(agent_name)
        
        if not agent:
            agent_name = "triage"  # Fallback to triage
            agent = self.factory.get_agent(agent_name)
        
        # Prepare input for the agent (include conversation context)
        agent_input = self._prepare_agent_input(request.message, history)
        
        # Run the agent with tracing
        with trace(workflow_name="Agent Chat", group_id=conversation_id):
            result = await Runner.run(agent, agent_input)
        
        # Add agent response to history
        assistant_message = ChatMessage(
            role="assistant",
            content=str(result.final_output),
            timestamp=datetime.now().isoformat()
        )
        self.store.add_message(conversation_id, assistant_message)
        
        # Get tool info for metadata
        tool_info = self.factory.get_tool_info()
        
        return AgentChatResponse(
            response=str(result.final_output),
            conversation_id=conversation_id,
            agent_used=agent_name,
            handoff_occurred=False,  # Will be True when we implement handoffs
            metadata={
                "model_used": agent.model,
                "tools_available": tool_info.get("total_tools", 0),
                "tool_categories": tool_info.get("categories", [])
            }
        )
    
    async def chat_stream(self, request: AgentChatRequest) -> AsyncGenerator[StreamingChatResponse, None]:
        """
        Handle a streaming chat request with the agent system.
        
        This method provides true streaming using Runner.run_streamed() while
        maintaining the same triage pattern as the regular chat method.
        """
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = self.store.get_conversation(conversation_id)
        
        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        self.store.add_message(conversation_id, user_message)
        
        # Determine which agent to use (same logic as regular chat)
        agent_name = request.agent_type or "triage"
        agent = self.factory.get_agent(agent_name)
        
        if not agent:
            agent_name = "triage"  # Fallback to triage
            agent = self.factory.get_agent(agent_name)
        
        # Prepare input for the agent (include conversation context)
        agent_input = self._prepare_agent_input(request.message, history)
        
        # Track the complete response for conversation history
        complete_response = ""
        
        # Run the agent with streaming and tracing
        with trace(workflow_name="Agent Chat Stream", group_id=conversation_id):
            result = Runner.run_streamed(agent, agent_input)
            
            async for event in result.stream_events():
                # Handle raw response events (text deltas)
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    chunk = event.data.delta
                    complete_response += chunk
                    
                    yield StreamingChatResponse(
                        chunk=chunk,
                        conversation_id=conversation_id,
                        is_complete=False,
                        agent_used=agent_name
                    )
                
                # Handle completion
                elif event.type == "run_item_stream_event" and event.item.type == "message_output_item":
                    # This indicates the response is complete
                    yield StreamingChatResponse(
                        chunk="",
                        conversation_id=conversation_id,
                        is_complete=True,
                        agent_used=agent_name
                    )
        
        # Add the complete response to conversation history
        assistant_message = ChatMessage(
            role="assistant",
            content=complete_response,
            timestamp=datetime.now().isoformat()
        )
        self.store.add_message(conversation_id, assistant_message)
    
    def _prepare_agent_input(self, current_message: str, history: List[ChatMessage]) -> str:
        """Prepare input for the agent including conversation context."""
        
        if not history:
            return current_message
        
        # Include recent conversation context (last 5 messages)
        recent_history = history[-5:] if len(history) > 5 else history
        
        context_parts = ["Previous conversation context:"]
        for msg in recent_history[:-1]:  # Exclude the current message we just added
            context_parts.append(f"{msg.role}: {msg.content}")
        
        context_parts.append(f"\nCurrent user message: {current_message}")
        
        return "\n".join(context_parts)
    
    async def get_conversation_history(self, conversation_id: str) -> ConversationHistory:
        """Get conversation history."""
        messages = self.store.get_conversation(conversation_id)
        
        if not messages:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=messages,
            created_at=messages[0].timestamp if messages else datetime.now().isoformat(),
            updated_at=messages[-1].timestamp if messages else datetime.now().isoformat()
        )
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with summary information."""
        conversation_ids = self.store.get_conversation_ids()
        conversations = []
        
        for conv_id in conversation_ids:
            messages = self.store.get_conversation(conv_id)
            if messages:
                # Get the first user message as a summary
                first_user_message = next((msg for msg in messages if msg.role == "user"), None)
                last_message = messages[-1] if messages else None
                
                conversation_summary = {
                    "id": conv_id,
                    "title": None,  # Could be derived from first message or set explicitly
                    "last_message_summary": first_user_message.content[:50] + "..." if first_user_message and len(first_user_message.content) > 50 else first_user_message.content if first_user_message else "No messages",
                    "updated_at": last_message.timestamp if last_message else datetime.now().isoformat(),
                    "message_count": len(messages)
                }
                conversations.append(conversation_summary)
        
        # Sort by updated_at descending (most recent first)
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    def list_available_agents(self) -> List[str]:
        """List all available agents."""
        return self.factory.list_agents()
    
    def get_tool_information(self) -> Dict[str, Any]:
        """Get information about available tools."""
        return self.factory.get_tool_info()

# Global service instance
agent_service = AgentService() 