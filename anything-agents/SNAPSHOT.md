.
├── app/                         # Main application source code package
│   ├── __init__.py              # Initializes the 'app' package
│   ├── api/                     # Versioned HTTP presentation layer
│   │   ├── __init__.py
│   │   ├── dependencies/        # FastAPI dependency utils (auth, pagination)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   ├── errors.py            # Global exception handlers for consistent error payloads
│   │   ├── models/              # Shared API-facing Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   ├── router.py            # Aggregates and mounts API versions
│   │   └── v1/                  # Version 1 API surface
│   │       ├── __init__.py
│   │       ├── router.py        # V1 aggregate router
│   │       ├── agents/          # Agent catalogue endpoints & schemas
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       ├── auth/            # Authentication endpoints
│   │       │   ├── __init__.py
│   │       │   └── router.py
│   │       ├── chat/            # Chat interaction endpoints & schemas
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       ├── conversations/   # Conversation management endpoints & schemas
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       └── tools/           # Tool catalogue endpoints
│   │           ├── __init__.py
│   │           └── router.py
│   ├── clients/                 # For external API clients (e.g., database, third-party services)
│   │   └── __init__.py
│   ├── core/                    # Core application logic (config, security)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── domain/                  # Domain entities and repository interfaces
│   │   ├── __init__.py
│   │   └── conversations.py
│   ├── infrastructure/          # Infrastructure adapters (persistence, OpenAI runner)
│   │   ├── __init__.py
│   │   ├── openai/
│   │   │   ├── __init__.py
│   │   │   └── runner.py
│   │   └── persistence/
│   │       ├── __init__.py
│   │       └── conversations/
│   │           ├── __init__.py
│   │           └── in_memory.py
│   ├── middleware/              # Custom FastAPI middleware
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── presentation/            # Non-versioned presentation layer (health endpoints)
│   │   ├── __init__.py
│   │   └── health.py
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   └── agent_service.py
│   └── utils/                   # Utility functions and helper modules
│       ├── __init__.py
│       └── tools/
│           ├── __init__.py
│           ├── registry.py
│           └── web_search.py
├── main.py                      # FastAPI application factory and entry point
└── tests/                       # Contains all application tests
    ├── __init__.py
    ├── test_agents.py           # Endpoint & service tests for agents/conversations
    ├── test_health.py           # Tests for the /health and /health/ready endpoints
    ├── test_streaming.py        # Client script to test streaming chat functionality
    └── test_tools.py            # Tests for the agent tool registry and individual tools
