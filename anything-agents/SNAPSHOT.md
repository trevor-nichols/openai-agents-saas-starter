
.
├── .pytest_cache/             # Cache directory for pytest runs
│   ├── CACHEDIR.TAG           # Pytest cache directory tag file
│   └── v/                     # Subdirectory for pytest cache data
├── alembic/                   # Contains Alembic database migration scripts
│   ├── env.py                 # Alembic environment configuration for running migrations
│   ├── script.py.mako         # Template for generating new Alembic migration scripts
│   └── versions/              # Directory for individual database migration scripts
│       ├── 20251106_120000_create_conversation_and_billing_tables.py # Initial migration to create core application tables
│       ├── 20251106_220000_add_service_account_tokens.py # Migration to add a table for service account refresh tokens
│       ├── 20251106_230500_hash_refresh_token_column.py # Renames refresh_token column to *_hash and truncates plaintext rows
│       └── __init__.py          # Makes the `versions` directory a Python package
├── alembic.ini                # Configuration file for Alembic database migrations
├── app/                       # Main application source code directory
│   ├── __init__.py            # Initializes the `app` package
│   ├── api/                   # Contains all API-related code (routers, schemas, dependencies)
│   │   ├── __init__.py          # Initializes the `api` package
│   │   ├── dependencies/        # FastAPI dependency injection helpers
│   │   │   ├── __init__.py      # Exposes shared dependency helpers
│   │   │   ├── auth.py          # Dependency for requiring an authenticated user
│   │   │   ├── common.py        # Shared dependencies like pagination parameters
│   │   │   └── tenant.py        # Dependencies for multi-tenant context and role enforcement
│   │   ├── errors.py            # Centralized API exception handlers
│   │   ├── models/              # Pydantic models for API requests and responses
│   │   │   ├── __init__.py      # Initializes the `models` package
│   │   │   ├── auth.py          # Pydantic models for authentication requests/responses
│   │   │   └── common.py        # Common API response models like SuccessResponse and Pagination
│   │   ├── router.py            # Top-level API router that aggregates versioned routers
│   │   └── v1/                  # Code for version 1 of the API
│   │       ├── __init__.py        # Initializes the `v1` package
│   │       ├── agents/            # Endpoints related to the agent catalog
│   │       │   ├── __init__.py    # Initializes the `agents` package
│   │       │   ├── router.py      # FastAPI router for agent catalog endpoints
│   │       │   └── schemas.py     # Pydantic schemas for agent-related API responses
│   │       ├── auth/              # Endpoints for authentication and token management
│   │       │   ├── __init__.py    # Initializes the `auth` package
│   │       │   └── router.py      # FastAPI router for authentication and service account token issuance
│   │       ├── billing/           # Endpoints for billing and subscription management
│   │       │   ├── __init__.py    # Initializes the `billing` package
│   │       │   ├── router.py      # FastAPI router for billing and subscription endpoints
│   │       │   └── schemas.py     # Pydantic schemas for billing API requests/responses
│   │       ├── chat/              # Endpoints for interacting with agents
│   │       │   ├── __init__.py    # Initializes the `chat` package
│   │       │   ├── router.py      # FastAPI router for synchronous and streaming chat endpoints
│   │       │   └── schemas.py     # Pydantic schemas for chat requests and responses
│   │       ├── conversations/     # Endpoints for managing conversation history
│   │       │   ├── __init__.py    # Initializes the `conversations` package
│   │       │   ├── router.py      # FastAPI router for listing, getting, and deleting conversations
│   │       │   └── schemas.py     # Pydantic schemas for conversation history and summaries
│   │       ├── router.py          # Aggregates all v1 API endpoint routers
│   │       └── tools/             # Endpoint for listing available agent tools
│   │           ├── __init__.py    # Initializes the `tools` package
│   │           └── router.py      # FastAPI router for listing available tools
│   ├── cli/                     # Command-line interface scripts
│   │   ├── __init__.py          # Initializes the `cli` package
│   │   └── auth_cli.py          # CLI tool for managing auth tokens and signing keys
│   ├── core/                    # Core application logic, configuration, and security
│   │   ├── __init__.py          # Initializes the `core` package
│   │   ├── config.py            # Pydantic-based application settings management
│   │   ├── keys.py              # Ed25519 signing key lifecycle management and storage
│   │   ├── security.py          # JWT token creation, verification, and password hashing
│   │   ├── service_accounts.py  # Loads and manages service account definitions from YAML
│   │   └── service_accounts.yaml # Configuration file defining available service accounts
│   ├── domain/                  # Core business models and repository interfaces (contracts)
│   │   ├── __init__.py          # Initializes the `domain` package
│   │   ├── auth.py              # Domain models and repository protocol for authentication
│   │   ├── billing.py           # Domain models and repository protocol for billing
│   │   └── conversations.py     # Domain models and repository protocol for conversations
│   ├── infrastructure/          # Adapters for external systems (DB, caches, 3rd party APIs)
│   │   ├── __init__.py          # Initializes the `infrastructure` package
│   │   ├── db/                  # Database connection and session management
│   │   │   ├── __init__.py      # Exposes key database helper functions
│   │   │   ├── engine.py        # Manages the SQLAlchemy async engine and session factory
│   │   │   └── session.py       # FastAPI dependency for providing database sessions to endpoints
│   │   ├── openai/              # Wrappers for OpenAI-related libraries
│   │   │   ├── __init__.py      # Initializes the `openai` package
│   │   │   └── runner.py        # Wrapper around the OpenAI Agents SDK runner
│   │   ├── persistence/         # Concrete repository implementations for data storage
│   │   │   ├── __init__.py      # Initializes the `persistence` package
│   │   │   ├── auth/            # Persistence logic for authentication data
│   │   │   │   ├── cache.py     # Redis-backed cache for refresh tokens
│   │   │   │   ├── models.py    # SQLAlchemy ORM model for service account tokens
│   │   │   │   └── repository.py # Postgres-backed implementation of the refresh token repository
│   │   │   ├── billing/         # Persistence logic for billing data
│   │   │   │   ├── __init__.py  # Exposes billing repository implementations
│   │   │   │   ├── in_memory.py # In-memory implementation of the billing repository
│   │   │   │   └── postgres.py  # Postgres-backed implementation of the billing repository
│   │   │   ├── conversations/   # Persistence logic for conversation data
│   │   │   │   ├── __init__.py  # Exposes conversation repository implementations
│   │   │   │   ├── in_memory.py # In-memory implementation of the conversation repository
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for conversation and billing tables
│   │   │   │   └── postgres.py  # Postgres-backed implementation of the conversation repository
│   │   │   ├── models/          # Base models for persistence layer
│   │   │   │   └── base.py      # Shared SQLAlchemy declarative base and helper functions
│   │   │   └── security/        # Security-related infrastructure components
│   │   │       ├── nonce_store.py # Replay protection nonce store (in-memory or Redis)
│   │   │       ├── vault.py     # Client for HashiCorp Vault's Transit engine
│   │   │       └── vault_kv.py  # Client for HashiCorp Vault's KV secret store
│   ├── middleware/              # Custom FastAPI middleware
│   │   ├── __init__.py          # Initializes the `middleware` package
│   │   └── logging.py           # Middleware for request/response logging with correlation IDs
│   ├── presentation/            # Non-API endpoints (e.g., health checks)
│   │   ├── __init__.py          # Initializes the `presentation` package
│   │   ├── health.py            # Liveness and readiness health check endpoints
│   │   └── well_known.py        # Endpoint for exposing JWKS document
│   ├── services/                # Business logic services that orchestrate domain objects
│   │   ├── __init__.py          # Initializes the `services` package
│   │   ├── agent_service.py     # Core service for orchestrating agent interactions
│   │   ├── auth_service.py      # Service for issuing and managing service account tokens
│   │   ├── billing_service.py   # Service for managing subscriptions and billing logic
│   │   ├── conversation_service.py # Service for managing conversation history persistence
│   │   └── payment_gateway.py   # Abstraction for payment providers like Stripe
│   └── utils/                   # General utility functions and helpers
│       ├── __init__.py          # Initializes the `utils` package
│       └── tools/               # Agent tool definitions and registry
│           ├── __init__.py      # Exposes tool registry components
│           ├── registry.py      # Central registry for managing agent tools
│           └── web_search.py    # Web search tool implementation using Tavily API
├── main.py                    # Main FastAPI application entry point and configuration
└── tests/                     # Contains all tests for the application
    ├── __init__.py            # Initializes the `tests` package and describes test structure
    ├── contract/              # Tests for API boundaries and external contracts
    │   ├── test_agents_api.py   # Contract tests for the agent catalog and chat APIs
    │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance via CLI
    │   ├── test_health_endpoints.py # Tests for the `/health` and `/health/ready` endpoints
    │   └── test_streaming_manual.py # Manual smoke test script for the SSE streaming chat endpoint
    ├── integration/           # Tests requiring external resources like a database
    │   ├── __init__.py        # Initializes the `integration` test package
    │   └── test_postgres_migrations.py # Integration tests for Alembic migrations and Postgres repositories
    └── unit/                  # Fast unit tests with no external dependencies
        ├── test_auth_domain.py # Unit tests for refresh-token hashing helpers
        ├── test_auth_service.py # Unit tests for the authentication service logic
        ├── test_billing_service.py # Unit tests for the billing service logic
        ├── test_config.py     # Unit tests for application settings validation
        ├── test_keys.py       # Unit tests for signing key generation and management logic
        ├── test_keys_cli.py   # Unit tests for the key management CLI commands
        ├── test_nonce_store.py # Unit tests for the replay-protection nonce store
        ├── test_tools.py      # Unit tests for the agent tool registry and definitions
        ├── test_vault_client.py # Unit tests for the Vault Transit client
        └── test_vault_kv.py   # Unit tests for the Vault KV secrets client
