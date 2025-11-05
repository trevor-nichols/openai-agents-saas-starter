# File: test_streaming.py
# Purpose: Test script to demonstrate streaming functionality
# Dependencies: httpx, asyncio
# Used by: Manual testing of streaming endpoints

import asyncio
import json
import socket

import httpx
import pytest


def _api_server_available(host: str = "localhost", port: int = 8000, timeout: float = 0.5) -> bool:
    """Return True if the agent API server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _api_server_available(),
    reason="Streaming smoke test requires a running agent API server on localhost:8000.",
)

async def test_streaming_chat():
    """Test the streaming chat endpoint."""
    
    url = "http://localhost:8000/api/v1/agents/chat/stream"
    
    chat_request = {
        "message": "Tell me a detailed story about a robot learning to paint",
        "agent_type": "triage"
    }
    
    print("🚀 Starting streaming chat test...")
    print(f"📝 Request: {chat_request['message']}")
    print("📡 Streaming response:")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", 
            url, 
            json=chat_request,
            headers={"Accept": "text/event-stream"}
        ) as response:
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(await response.aread())
                return
            
            complete_response = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        
                        chunk = data.get("chunk", "")
                        is_complete = data.get("is_complete", False)
                        conversation_id = data.get("conversation_id", "")
                        agent_used = data.get("agent_used", "")
                        
                        if chunk:
                            print(chunk, end="", flush=True)
                            complete_response += chunk
                        
                        if is_complete:
                            print("\n" + "-" * 50)
                            print("✅ Stream complete!")
                            print(f"🤖 Agent used: {agent_used}")
                            print(f"💬 Conversation ID: {conversation_id}")
                            print(f"📊 Total characters: {len(complete_response)}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        print(f"Raw line: {line}")

async def test_regular_chat():
    """Test the regular (non-streaming) chat endpoint for comparison."""
    
    url = "http://localhost:8000/api/v1/agents/chat"
    
    chat_request = {
        "message": "What's the weather like today?",
        "agent_type": "triage"
    }
    
    print("\n🔄 Testing regular chat for comparison...")
    print(f"📝 Request: {chat_request['message']}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=chat_request)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data['response']}")
            print(f"🤖 Agent used: {data['agent_used']}")
            print(f"💬 Conversation ID: {data['conversation_id']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

async def main():
    """Main test function."""
    print("🧪 Testing Agent Streaming System")
    print("=" * 60)
    
    # Test streaming
    await test_streaming_chat()
    
    # Test regular chat
    await test_regular_chat()
    
    print("\n🎉 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
