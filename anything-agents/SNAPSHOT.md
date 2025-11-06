.
├── .pytest_cache              # Cache directory for pytest runs
│   ├── CACHEDIR.TAG           # Pytest cache directory tag file
│   └── v                      # Pytest cache data subdirectory
├── alembic                    # Contains Alembic database migration scripts
│   ├── env.py                 # Alembic environment configuration for running migrations
│   ├── script.py.mako         # Mako template for generating new migration scripts
│   └── versions               # Directory for individual migration files
│       ├── 20251106_120000_create_conversation_and_billing_tables.py # Initial migration to create conversation and billing tables
│       └── __init__.py        # Makes the 'versions' directory a Python package
├── alembic.ini                # Configuration file for Alembic
├── app                        # Main application source code
│   ├── __init__.py            # Initializes the 'app' package
│   ├── api                    # Contains all API-related code (endpoints, schemas, dependencies)
│   │   ├── __init__.py        # Initializes the 'api' package
│   │   ├── dependencies       # FastAPI dependency injection helpers
│   │   │   ├── __init__.py    # Exposes shared dependency helpers
│   │   │   ├── auth.py        # Dependency for requiring an authenticated user
│   │   │   ├── common.py      # Shared dependencies like pagination parameters
│   │   │   └── tenant.py      # Dependencies for handling multi-tenancy context
│   │   ├── errors.py          # Centralized exception handlers for the API
│   │   ├── models             # Pydantic models used across the API
│   │   │   ├── __init__.py    # Initializes the 'models' package
│   │   │   ├── auth.py        # Pydantic models for authentication (Token, UserLogin, etc.)
│   │   │   └── common.py      # Common Pydantic models like Success/Error responses
│   │   ├── router.py          # Top-level API router that aggregates versioned routers
│   │   └── v1                 # Contains the version 1 implementation of the API
│   │       ├── __init__.py    # Initializes the 'v1' package
│   │       ├── agents         # Endpoints related to the agent catalog
│   │       │   ├── __init__.py # Initializes the 'agents' API package
│   │       │   ├── router.py  # FastAPI router for listing agents and getting their status
│   │       │   └── schemas.py # Pydantic schemas for agent-related API responses
│   │       ├── auth           # Authentication-related endpoints
│   │       │   ├── __init__.py # Initializes the 'auth' API package
│   │       │   └── router.py  # FastAPI router for token creation and user info
│   │       ├── billing        # Endpoints for managing billing plans and subscriptions
│   │       │   ├── __init__.py # Initializes the 'billing' API package
│   │       │   ├── router.py  # FastAPI router for plans, subscriptions, and usage
│   │       │   └── schemas.py # Pydantic schemas for billing API requests and responses
│   │       ├── chat           # Endpoints for interacting with agents
│   │       │   ├── __init__.py # Initializes the 'chat' API package
│   │       │   ├── router.py  # FastAPI router for standard and streaming chat responses
│   │       │   └── schemas.py # Pydantic schemas for chat requests and responses
│   │       ├── conversations  # Endpoints for managing conversation history
│   │       │   ├── __init__.py # Initializes the 'conversations' API package
│   │       │   ├── router.py  # FastAPI router for listing, getting, and deleting conversations
│   │       │   └── schemas.py # Pydantic schemas for conversation history and summaries
│   │       ├── router.py      # Aggregates all v1 API routers
│   │       └── tools          # Endpoints related to available agent tools
│   │           ├── __init__.py # Initializes the 'tools' API package
│   │           └── router.py  # FastAPI router for listing available agent tools
│   ├── core                   # Core application logic, configuration, and security
│   │   ├── __init__.py        # Initializes the 'core' package
│   │   ├── config.py          # Application settings management using Pydantic
│   │   └── security.py        # JWT token handling and password hashing utilities
│   ├── domain                 # Business logic, domain models, and repository interfaces
│   │   ├── __init__.py        # Initializes the 'domain' package
│   │   ├── billing.py         # Domain models and repository protocol for billing
│   │   └── conversations.py   # Domain models and repository protocol for conversations
│   ├── infrastructure         # Implementation of external concerns like databases and APIs
│   │   ├── __init__.py        # Initializes the 'infrastructure' package
│   │   ├── db                 # Database connection and session management
│   │   │   ├── __init__.py    # Exposes key database helpers
│   │   │   ├── engine.py      # Manages the async SQLAlchemy engine and session factory
│   │   │   └── session.py     # FastAPI dependency for providing database sessions
│   │   ├── openai             # Wrappers for the OpenAI SDK
│   │   │   ├── __init__.py    # Initializes the 'openai' infrastructure package
│   │   │   └── runner.py      # Wrapper for the OpenAI Agents SDK runner
│   │   └── persistence        # Concrete implementations of the domain repository protocols
│   │       ├── __init__.py    # Initializes the 'persistence' package
│   │       ├── billing        # Implementations of the BillingRepository protocol
│   │       │   ├── __init__.py # Exposes billing repository implementations
│   │       │   ├── in_memory.py # In-memory implementation of the billing repository
│   │       │   └── postgres.py # PostgreSQL implementation of the billing repository
│   │       └── conversations  # Implementations of the ConversationRepository protocol
│   │           ├── __init__.py # Exposes conversation repository implementations
│   │           ├── in_memory.py # In-memory implementation of the conversation repository
│   │           ├── models.py  # SQLAlchemy ORM models for all database tables
│   │           └── postgres.py # PostgreSQL implementation of the conversation repository
│   ├── middleware             # Custom FastAPI middleware
│   │   ├── __init__.py        # Initializes the 'middleware' package
│   │   └── logging.py         # Middleware for logging requests and responses
│   ├── presentation           # Non-API endpoints, like health checks
│   │   ├── __init__.py        # Initializes the 'presentation' package
│   │   └── health.py          # FastAPI router for /health and /health/ready endpoints
│   ├── services               # Service layer orchestrating application logic
│   │   ├── __init__.py        # Initializes the 'services' package
│   │   ├── agent_service.py   # Core service for orchestrating agent interactions
│   │   ├── billing_service.py # Service for managing billing and subscriptions
│   │   ├── conversation_service.py # Service for managing conversation history
│   │   └── payment_gateway.py # Abstraction (protocol) for payment providers like Stripe
│   └── utils                  # Utility functions and helper modules
│       ├── __init__.py        # Initializes the 'utils' package
│       └── tools              # Agent tool management and definitions
│           ├── __init__.py    # Exposes tool registry components
│           ├── registry.py    # Central registry for managing agent tools
│           └── web_search.py  # Implements a web search tool using the Tavily API
├── main.py                    # Main entry point for the FastAPI application
└── tests                      # Contains all automated tests for the application
    ├── __init__.py            # Initializes the 'tests' package
    ├── integration            # Integration tests requiring external services
    │   ├── __init__.py        # Initializes the 'integration' tests package
    │   └── test_postgres_migrations.py # Tests database migrations and Postgres repositories
    ├── test_agents.py         # Tests for agent-related endpoints and services
    ├── test_billing.py        # Tests for the billing service and related components
    ├── test_health.py         # Tests for the health and readiness check endpoints
    ├── test_streaming.py      # Manual/smoke test for the streaming chat endpoint
    └── test_tools.py          # Tests for the tool registry and tool implementations