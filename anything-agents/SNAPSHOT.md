.
├── .pytest_cache              # Pytest cache directory for speeding up test runs
│   ├── CACHEDIR.TAG           # Pytest cache directory tag file
│   └── v                      # Subdirectory for pytest cache data
├── alembic                    # Contains Alembic database migration scripts and configuration
│   ├── env.py                 # Alembic environment configuration for running migrations
│   ├── script.py.mako         # Template for generating new Alembic migration scripts
│   └── versions               # Directory for individual database migration scripts
│       ├── 0e52ba5ab089_idp_user_tables.py # Alembic migration to add comprehensive user and authentication tables
│       ├── 20251106_120000_create_conversation_and_billing_tables.py # Alembic migration for initial conversation and billing tables
│       ├── 20251106_220000_add_service_account_tokens.py # Alembic migration to add a table for service account refresh tokens
│       ├── 20251106_230500_hash_refresh_token_column.py # Alembic migration to hash the refresh token column for security
│       ├── 20251106_235500_add_signing_kid_column.py # Alembic migration to add a key ID column to the tokens table
│       └── __init__.py        # Makes the `versions` directory a Python package
├── alembic.ini                # Configuration file for the Alembic database migration tool
├── app                        # Main application source code package
│   ├── __init__.py            # Initializes the `app` package
│   ├── api                    # Contains all API-related code (routers, schemas, dependencies)
│   │   ├── __init__.py        # Initializes the `api` package
│   │   ├── dependencies       # FastAPI dependency injection helpers
│   │   │   ├── __init__.py    # Exposes shared dependency helpers
│   │   │   ├── auth.py        # Authentication dependencies, like `require_current_user`
│   │   │   ├── common.py      # Common dependencies like pagination parameters
│   │   │   └── tenant.py      # Dependencies for handling multi-tenancy context
│   │   ├── errors.py          # Centralized API exception handling configuration
│   │   ├── models             # Pydantic models for API request/response bodies (schemas)
│   │   │   ├── __init__.py    # Initializes the `models` package
│   │   │   ├── auth.py        # Pydantic models for authentication requests and responses
│   │   │   └── common.py      # Common API response models like `SuccessResponse` and `ErrorResponse`
│   │   ├── router.py          # Top-level API router that includes the versioned routers
│   │   └── v1                 # Contains the V1 version of the API
│   │       ├── __init__.py    # Initializes the `v1` API package
│   │       ├── agents         # API endpoints related to agent management
│   │       │   ├── __init__.py # Initializes the `agents` API package
│   │       │   ├── router.py  # FastAPI router for agent catalog endpoints
│   │       │   └── schemas.py # Pydantic schemas for agent-related API responses
│   │       ├── auth           # API endpoints for authentication and token management
│   │       │   ├── __init__.py # Initializes the `auth` API package
│   │       │   └── router.py  # FastAPI router for authentication endpoints (token, refresh, etc.)
│   │       ├── billing        # API endpoints for billing and subscription management
│   │       │   ├── __init__.py # Initializes the `billing` API package
│   │       │   ├── router.py  # FastAPI router for billing and subscription endpoints
│   │       │   └── schemas.py # Pydantic schemas for billing-related requests and responses
│   │       ├── chat           # API endpoints for chat interactions with agents
│   │       │   ├── __init__.py # Initializes the `chat` API package
│   │       │   ├── router.py  # FastAPI router for chat and streaming chat endpoints
│   │       │   └── schemas.py # Pydantic schemas for chat requests and responses
│   │       ├── conversations  # API endpoints for managing conversation history
│   │       │   ├── __init__.py # Initializes the `conversations` API package
│   │       │   ├── router.py  # FastAPI router for listing, getting, and deleting conversations
│   │       │   └── schemas.py # Pydantic schemas for conversation history and summaries
│   │       ├── router.py      # Aggregates all V1 API endpoint routers
│   │       └── tools          # API endpoints related to agent tools
│   │           ├── __init__.py # Initializes the `tools` API package
│   │           └── router.py  # FastAPI router for listing available agent tools
│   ├── cli                    # Command-line interface tools for the application
│   │   ├── __init__.py        # Initializes the `cli` package
│   │   └── auth_cli.py        # Command-line utility for auth tasks like issuing tokens and managing keys
│   ├── core                   # Core application logic, configuration, and security
│   │   ├── __init__.py        # Initializes the `core` package
│   │   ├── config.py          # Pydantic-based settings management from environment variables
│   │   ├── keys.py            # Manages cryptographic key lifecycle (generation, storage, rotation)
│   │   ├── security.py        # Handles JWT creation/verification and password hashing
│   │   ├── service_accounts.py # Defines and loads the service account catalog
│   │   └── service_accounts.yaml # YAML configuration defining available service accounts
│   ├── domain                 # Defines core business models and repository interfaces (contracts)
│   │   ├── __init__.py        # Initializes the `domain` package
│   │   ├── auth.py            # Domain models and repository contract for authentication
│   │   ├── billing.py         # Domain models and repository contract for billing
│   │   ├── conversations.py   # Domain models and repository contract for conversations
│   │   └── users.py           # Domain models for human users and related DTOs
│   ├── infrastructure         # Implementation of external concerns like databases and APIs
│   │   ├── __init__.py        # Initializes the `infrastructure` package
│   │   ├── db                 # Database connection and session management
│   │   │   ├── __init__.py    # Exposes database helper functions
│   │   │   ├── engine.py      # Manages the SQLAlchemy async engine and migrations
│   │   │   └── session.py     # FastAPI dependency for providing database sessions
│   │   ├── openai             # Wrappers for the OpenAI SDK
│   │   │   ├── __init__.py    # Initializes the `openai` infrastructure package
│   │   │   └── runner.py      # Wrapper for the OpenAI Agents SDK runner
│   │   ├── persistence        # Implementation of the domain repository contracts
│   │   │   ├── __init__.py    # Initializes the `persistence` package
│   │   │   ├── auth           # Persistence logic for authentication
│   │   │   │   ├── cache.py   # Redis cache implementation for refresh tokens
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for users, tokens, and auth entities
│   │   │   │   └── repository.py # Postgres implementation of the refresh token repository
│   │   │   ├── billing        # Persistence logic for billing
│   │   │   │   ├── __init__.py # Exposes billing repository implementations
│   │   │   │   ├── in_memory.py # In-memory implementation of the billing repository
│   │   │   │   └── postgres.py # Postgres implementation of the billing repository
│   │   │   ├── conversations  # Persistence logic for conversations
│   │   │   │   ├── __init__.py # Exposes conversation repository implementations
│   │   │   │   ├── in_memory.py # In-memory implementation of the conversation repository
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for conversations and billing entities
│   │   │   │   └── postgres.py # Postgres implementation of the conversation repository
│   │   │   └── models         # Base models for persistence
│   │   │       └── base.py    # Shared SQLAlchemy declarative base and helper functions
│   │   └── security           # Security-related infrastructure implementations
│   │       ├── nonce_store.py # Nonce store for replay attack protection
│   │       ├── vault.py       # Client for HashiCorp Vault's Transit secret engine
│   │       └── vault_kv.py    # Client for HashiCorp Vault's KV secret engine
│   ├── middleware             # Custom FastAPI middleware
│   │   ├── __init__.py        # Initializes the `middleware` package
│   │   └── logging.py         # Middleware for request/response logging with correlation IDs
│   ├── observability          # Code for logging, metrics, and tracing
│   │   ├── __init__.py        # Initializes the `observability` package
│   │   ├── logging.py         # Structured logging helper for observability events
│   │   └── metrics.py         # Prometheus metrics definitions for the application
│   ├── presentation           # Non-API endpoints like health checks and metrics
│   │   ├── __init__.py        # Initializes the `presentation` package
│   │   ├── health.py          # Liveness and readiness probe endpoints
│   │   ├── metrics.py         # Prometheus metrics scrape endpoint
│   │   └── well_known.py      # Endpoints for `.well-known` URIs, like JWKS
│   ├── services               # Business logic layer coordinating domain objects and infrastructure
│   │   ├── __init__.py        # Initializes the `services` package
│   │   ├── agent_service.py   # Core service for orchestrating agent interactions
│   │   ├── auth_service.py    # Service for handling authentication logic, like token issuance
│   │   ├── billing_service.py # Service for managing billing and subscription logic
│   │   ├── conversation_service.py # Service for managing conversation history and state
│   │   └── payment_gateway.py # Abstraction for payment providers like Stripe
│   └── utils                  # General utility modules and helpers
│       ├── __init__.py        # Initializes the `utils` package
│       └── tools              # Agent tool definitions and registry
│           ├── __init__.py    # Exposes tool registry and specific tools
│           ├── registry.py    # Central registry for managing agent tools
│           └── web_search.py  # Implements a web search tool using the Tavily API
├── main.py                    # Main FastAPI application entry point
└── tests                      # Contains all tests for the application
    ├── __init__.py            # Initializes the `tests` package
    ├── conftest.py            # Shared pytest fixtures for the test suite
    ├── contract               # Tests for API contracts and external-facing behavior
    │   ├── test_agents_api.py # Contract tests for the agent management API endpoints
    │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance
    │   ├── test_health_endpoints.py # Contract tests for the health and readiness endpoints
    │   ├── test_metrics_endpoint.py # Contract tests for the Prometheus metrics endpoint
    │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming
    │   └── test_well_known.py # Contract tests for the `.well-known/jwks.json` endpoint
    ├── fixtures               # Test fixture data
    │   └── keysets            # Directory containing test keyset files
    ├── integration            # Tests requiring external services like a database
    │   ├── __init__.py        # Initializes the `integration` tests package
    │   └── test_postgres_migrations.py # Integration tests for Alembic migrations and Postgres repositories
    └── unit                   # Fast unit tests with no external dependencies
        ├── test_auth_domain.py # Unit tests for authentication domain logic
        ├── test_auth_service.py # Unit tests for the authentication service layer
        ├── test_billing_service.py # Unit tests for the billing service layer
        ├── test_config.py     # Unit tests for application configuration settings
        ├── test_keys.py       # Unit tests for cryptographic key management logic
        ├── test_keys_cli.py   # Unit tests for the key management CLI commands
        ├── test_metrics.py    # Unit tests for Prometheus metrics helpers
        ├── test_nonce_store.py # Unit tests for the nonce store implementation
        ├── test_security.py   # Unit tests for security utilities like token signing
        ├── test_tools.py      # Unit tests for agent tool registration and functionality
        ├── test_user_models.py # Unit tests for user-related SQLAlchemy ORM models
        ├── test_vault_client.py # Unit tests for the Vault Transit client
        └── test_vault_kv.py   # Unit tests for the Vault KV secrets client
