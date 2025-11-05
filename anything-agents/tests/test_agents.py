# File: tests/test_agents.py
# Purpose: Test cases for agent functionality
# Dependencies: pytest, fastapi.testclient, app modules
# Used by: pytest for testing agent interactions

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from app.schemas.agents import AgentChatRequest, AgentChatResponse

client = TestClient(app)

# =============================================================================
# AGENT ENDPOINT TESTS
# =============================================================================

def test_list_available_agents():
    """Test listing available agents."""
    response = client.get("/api/v1/agents/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "agents" in data["data"]
    assert len(data["data"]["agents"]) > 0

def test_get_agent_status():
    """Test getting agent status."""
    response = client.get("/api/v1/agents/agents/triage/status")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "triage"
    assert data["status"] == "active"

def test_get_nonexistent_agent_status():
    """Test getting status of non-existent agent."""
    response = client.get("/api/v1/agents/agents/nonexistent/status")
    assert response.status_code == 404

@patch('app.services.agent_service.Runner.run')
async def test_chat_with_agent(mock_runner):
    """Test chatting with an agent."""
    # Mock the agent response
    mock_result = AsyncMock()
    mock_result.final_output = "Hello! I'm here to help you."
    mock_runner.return_value = mock_result
    
    chat_request = {
        "message": "Hello, how are you?",
        "agent_type": "triage"
    }
    
    response = client.post("/api/v1/agents/chat", json=chat_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert data["agent_used"] == "triage"

def test_list_conversations():
    """Test listing conversations."""
    response = client.get("/api/v1/agents/conversations")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "conversation_ids" in data["data"]

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_agent_service_initialization():
    """Test that agent service initializes correctly."""
    from app.services.agent_service import agent_service
    
    # Check that agents are available
    agents = agent_service.list_available_agents()
    assert "triage" in agents
    assert "code_assistant" in agents
    assert "data_analyst" in agents

def test_conversation_store():
    """Test conversation storage functionality."""
    from app.services.agent_service import conversation_store
    from app.schemas.agents import ChatMessage
    
    # Test adding and retrieving messages
    conv_id = "test_conversation"
    message = ChatMessage(role="user", content="Test message")
    
    conversation_store.add_message(conv_id, message)
    retrieved = conversation_store.get_conversation(conv_id)
    
    assert len(retrieved) == 1
    assert retrieved[0].content == "Test message" 