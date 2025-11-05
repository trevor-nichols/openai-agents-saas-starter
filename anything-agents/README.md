# Anything Agents - Extensible AI Agent System

A FastAPI-based AI agent system built with the OpenAI Agents SDK, designed for easy extension from single agent to multiagent systems.

## 🚀 Features

- **Extensible Triage Pattern**: Start with a single main agent, easily add specialized agents
- **Conversation Management**: Persistent conversation history with context awareness
- **Streaming Support**: Real-time streaming responses for better UX
- **Multiple Agent Types**: Ready-to-activate specialized agents (code, data analysis, etc.)
- **RESTful API**: Clean, documented API endpoints
- **Type Safety**: Full Pydantic validation and type hints

## 🏗️ Architecture

### Current Implementation: Single Agent with Extension Points

```
User → Triage Agent (Main Chatbot)
         ↓
    [Future: Specialized Agents]
```

### Future Multiagent Capabilities

```
User → Triage Agent → Code Assistant
                   → Data Analyst  
                   → Research Agent
                   → Custom Agents
```

## 📁 Project Structure

```
anything-agents/
├── app/
│   ├── api/
│   │   ├── models/     # Public request/response schemas
│   │   ├── dependencies/ # Shared FastAPI dependencies
│   │   ├── errors.py   # Global exception handlers
│   │   └── v1/         # Versioned REST surface (`/api/v1/...`)
│   ├── core/           # Configuration and security
│   ├── domain/         # Domain objects and repository contracts
│   ├── infrastructure/ # External adapters (OpenAI runner, persistence)
│   ├── services/       # Business logic (Agent orchestration)
│   ├── middleware/     # Custom middleware
│   └── utils/          # Utility functions
├── tests/              # Test suite
└── main.py            # FastAPI application
```

## 🛠️ Setup

### 1. Install Tooling

We use [Hatch](https://hatch.pypa.io/) to manage virtual environments and scripts.

```bash
pipx install hatch  # or: pip install --user hatch
```

### 2. Create the Development Environment

```bash
hatch env create
```

This provisions a local virtualenv with all runtime and developer dependencies defined in `pyproject.toml`.

### 3. Environment Configuration

Copy `.env.example` to `.env.local` and configure:

```bash
# AI API Keys (at least one required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
XAI_API_KEY=your_xai_key

# Server Configuration
PORT=8000
DEBUG=True
SECRET_KEY=your_secret_key
```

### 4. Run the Application

```bash
hatch run serve
```

The API will be available at `http://localhost:8000`

### 5. Quality Checks

Run the standard backend quality gates before opening a PR:

```bash
hatch run lint
hatch run typecheck
hatch run pyright
hatch run test
```

## 🤖 Agent Types

### Current Agents

1. **Triage Agent** (Active)
   - Main conversational interface
   - Handles general queries
   - Routes to specialized agents (future)
   - Tools: time, conversation search

2. **Code Assistant** (Ready to activate)
   - Code review and debugging
   - Architecture suggestions
   - Best practices guidance

3. **Data Analyst** (Ready to activate)
   - Data interpretation
   - Statistical analysis
   - Visualization suggestions

## 📡 API Endpoints

### Chat with Agents

```bash
# Basic chat
POST /api/v1/chat
{
  "message": "Hello, how can you help me?",
  "agent_type": "triage",
  "conversation_id": "optional-uuid"
}

# Streaming chat
POST /api/v1/chat/stream
# Returns Server-Sent Events stream
```

### Conversation Management

```bash
# List conversations
GET /api/v1/conversations

# Get conversation history
GET /api/v1/conversations/{conversation_id}

# Clear conversation
DELETE /api/v1/conversations/{conversation_id}
```

### Agent Management

```bash
# List available agents
GET /api/v1/agents

# Get agent status
GET /api/v1/agents/{agent_name}/status
```

## 🔧 Extending to Multiagent System

### Option 1: Activate Existing Specialized Agents

Simply modify the triage agent's instructions to include handoffs:

```python
# In app/services/agent_service.py
self._agents["triage"] = Agent(
    name="Triage Assistant",
    instructions="""
    You are the main AI assistant. For coding questions, 
    handoff to the code assistant. For data questions, 
    handoff to the data analyst.
    """,
    handoffs=[
        self._agents["code_assistant"],
        self._agents["data_analyst"]
    ]
)
```

### Option 2: Add New Specialized Agents

```python
# Add to AgentFactory._initialize_agents()
self._agents["research_agent"] = Agent(
    name="Research Specialist",
    instructions="You specialize in research and fact-checking...",
    tools=[web_search_tool, citation_tool]
)
```

### Option 3: Agents as Tools Pattern

```python
# Use agents as tools instead of handoffs
orchestrator = Agent(
    name="Orchestrator",
    tools=[
        code_agent.as_tool("code_help", "Get coding assistance"),
        data_agent.as_tool("data_analysis", "Analyze data")
    ]
)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run agent-specific tests
pytest tests/test_agents.py

# Run with coverage
pytest --cov=app tests/
```

## 🔄 Migration Path: Single → Multiagent

### Phase 1: Single Agent (Current)
- ✅ Triage agent handles all requests
- ✅ Conversation management
- ✅ Extensible architecture in place

### Phase 2: Selective Handoffs
- Activate specific specialized agents
- Add handoff logic to triage agent
- Minimal code changes required

### Phase 3: Full Multiagent System
- Multiple active agents
- Complex routing logic
- Agent-to-agent communication

### Phase 4: Advanced Features
- Dynamic agent creation
- Agent learning and adaptation
- Custom tool integration

## 🎯 Example Usage

### Simple Chat

```python
import requests

response = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "Explain quantum computing in simple terms"
})

print(response.json()["response"])
```

### Conversation with Context

```python
# First message
response1 = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "I'm working on a Python web app"
})

conversation_id = response1.json()["conversation_id"]

# Follow-up with context
response2 = requests.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "What framework should I use?",
    "conversation_id": conversation_id
})
```

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies and the service package
COPY pyproject.toml .
COPY LICENSE .
COPY run.py .
COPY anything-agents ./anything-agents
RUN pip install --upgrade pip && pip install --no-cache-dir .

# Provide application defaults (optional)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    RELOAD=false

CMD ["anything-agents"]
```

### Production Considerations

- Use Redis for conversation storage
- Implement proper authentication
- Add rate limiting
- Monitor agent performance
- Set up logging and tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready to build something amazing with AI agents? Start with the single agent and scale to multiagent systems as your needs grow!** 🚀 
