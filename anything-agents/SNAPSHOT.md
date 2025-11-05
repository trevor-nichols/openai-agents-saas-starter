.
├── app/                         # Main application source code package
│   ├── __init__.py              # Initializes the 'app' package
│   ├── clients/                 # For external API clients (e.g., database, third-party services)
│   │   └── __init__.py          # Initializes the 'clients' package
│   ├── core/                    # Core application logic (config, security)
│   │   ├── __init__.py          # Initializes the 'core' package
│   │   ├── config.py            # Manages application settings from environment variables
│   │   └── security.py          # Handles authentication, JWT tokens, and password hashing
│   ├── middleware/              # Contains custom FastAPI middleware
│   │   ├── __init__.py          # Initializes the 'middleware' package
│   │   └── logging.py           # Middleware for logging requests and responses
│   ├── routers/                 # Defines the API endpoints (routes)
│   │   ├── __init__.py          # Initializes the 'routers' package
│   │   ├── agents.py            # API endpoints for AI agent interactions (chat, stream)
│   │   ├── api.py               # General-purpose API endpoints for the application
│   │   ├── auth.py              # Authentication endpoints for user login and token management
│   │   └── health.py            # Health and readiness check endpoints
│   ├── schemas/                 # Pydantic models for data validation and serialization
│   │   ├── __init__.py          # Initializes the 'schemas' package
│   │   ├── agents.py            # Pydantic schemas for agent-related requests and responses
│   │   ├── auth.py              # Pydantic schemas for authentication flows (login, tokens)
│   │   └── common.py            # Common Pydantic schemas (SuccessResponse, Pagination)
│   ├── services/                # Business logic layer
│   │   ├── __init__.py          # Initializes the 'services' package
│   │   └── agent_service.py     # Core service for managing AI agents, tools, and conversations
│   └── utils/                   # Utility functions and helper modules
│       ├── __init__.py          # Initializes the 'utils' package
│       └── tools/               # Manages tools that can be used by AI agents
│           ├── __init__.py      # Initializes the 'tools' package and exports key components
│           ├── registry.py      # A central registry for managing and organizing agent tools
│           └── web_search.py    # Implements a web search tool using the Tavily API
├── main.py                      # FastAPI application entry point and configuration
└── tests/                       # Contains all application tests
    ├── __init__.py              # Initializes the 'tests' package
    ├── test_agents.py           # Unit and integration tests for agent endpoints and services
    ├── test_health.py           # Tests for the /health and /health/ready endpoints
    ├── test_streaming.py        # A client script to test the streaming chat functionality
    └── test_tools.py            # Tests for the agent tool registry and individual tools