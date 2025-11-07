.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                  # Alembic environment setup for running migrations.
│   └── script.py.mako          # Template for generating new Alembic migration files.
├── alembic.ini                 # Configuration file for the Alembic database migration tool.
├── app/                        # Main source code for the FastAPI application.
│   ├── __init__.py             # Initializes the 'app' Python package.
│   ├── api/                    # Contains all API-related logic (routers, models, dependencies).
│   │   ├── __init__.py         # Initializes the 'api' package.
│   │   ├── dependencies/       # FastAPI dependency injection helpers.
│   │   │   ├── __init__.py     # Exposes shared dependency helpers for easy import.
│   │   │   ├── auth.py         # Authentication dependency to require a current logged-in user.
│   │   │   ├── common.py       # Shared dependencies like pagination parameters.
│   │   │   └── tenant.py       # Dependencies for handling multi-tenancy context and roles.
│   │   ├── errors.py           # Centralized exception handlers for the API layer.
│   │   ├── models/             # Pydantic models for API request/response validation.
│   │   │   ├── __init__.py     # Initializes the 'models' package.
│   │   │   ├── auth.py         # Pydantic models for authentication requests and responses.
│   │   │   └── common.py       # Common API response models (e.g., SuccessResponse, ErrorResponse).
│   │   ├── router.py           # Top-level API router, aggregates versioned routers.
│   │   └── v1/                 # Code for version 1 of the API.
│   │       ├── __init__.py     # Initializes the 'v1' API package.
│   │       ├── agents/         # Endpoints for managing and inspecting agents.
│   │       │   ├── __init__.py # Initializes the 'agents' API package.
│   │       │   ├── router.py   # API routes for listing agents and getting their status.
│   │       │   └── schemas.py  # Pydantic schemas for agent-related API responses.
│   │       ├── auth/           # Endpoints for user and service account authentication.
│   │       │   ├── __init__.py # Initializes the 'auth' API package.
│   │       │   └── router.py   # API routes for token issuance, refresh, and user info.
│   │       ├── billing/        # Endpoints for managing billing plans and subscriptions.
│   │       │   ├── __init__.py # Initializes the 'billing' API package.
│   │       │   ├── router.py   # API routes for billing plans and tenant subscriptions.
│   │       │   └── schemas.py  # Pydantic schemas for billing API requests and responses.
│   │       ├── chat/           # Endpoints for real-time and streaming chat with agents.
│   │       │   ├── __init__.py # Initializes the 'chat' API package.
│   │       │   ├── router.py   # API routes for synchronous and streaming chat interactions.
│   │       │   └── schemas.py  # Pydantic schemas for chat requests and responses.
│   │       ├── conversations/  # Endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the 'conversations' API package.
│   │       │   ├── router.py   # API routes for listing, retrieving, and deleting conversations.
│   │       │   └── schemas.py  # Pydantic schemas for conversation history and summaries.
│   │       ├── router.py       # Aggregates all v1 API routers into a single router.
│   │       └── tools/          # Endpoints for inspecting available agent tools.
│   │           ├── __init__.py # Initializes the 'tools' API package.
│   │           └── router.py   # API route for listing available agent tools.
│   ├── cli/                    # Command-line interface scripts for administration.
│   │   ├── __init__.py         # Initializes the 'cli' package.
│   │   └── auth_cli.py         # CLI for issuing service account tokens and managing signing keys.
│   ├── core/                   # Core application logic, configuration, and security primitives.
│   │   ├── __init__.py         # Initializes the 'core' package.
│   │   ├── config.py           # Pydantic-based settings management from environment variables.
│   │   ├── keys.py             # Manages the lifecycle of Ed25519 signing keys.
│   │   ├── security.py         # Handles JWT creation/verification and password hashing.
│   │   ├── service_accounts.py # Loads and manages the service account catalog from YAML.
│   │   └── service_accounts.yaml # Defines available service accounts and their permissions.
│   ├── domain/                 # Defines core business models and repository interfaces (contracts).
│   │   ├── __init__.py         # Initializes the 'domain' package.
│   │   ├── auth.py             # Domain models and repository contract for refresh tokens.
│   │   ├── billing.py          # Domain models and repository contract for billing.
│   │   ├── conversations.py    # Domain models and repository contract for conversations.
│   │   └── users.py            # Domain models and repository contract for users.
│   ├── infrastructure/         # Concrete implementations for external systems (DB, cache, APIs).
│   │   ├── __init__.py         # Initializes the 'infrastructure' package.
│   │   ├── db/                 # Database connection and session management.
│   │   │   ├── __init__.py     # Exposes key database helper functions.
│   │   │   ├── engine.py       # Manages the async SQLAlchemy engine and session factory.
│   │   │   └── session.py      # FastAPI dependency for providing database sessions to routes.
│   │   ├── openai/             # Wrappers for OpenAI SDKs and services.
│   │   │   ├── __init__.py     # Initializes the 'openai' infrastructure package.
│   │   │   └── runner.py       # Wrapper for the OpenAI Agents SDK runner.
│   │   ├── persistence/        # Concrete implementations of domain repository contracts.
│   │   │   ├── __init__.py     # Initializes the 'persistence' package.
│   │   │   ├── auth/           # Persistence implementations for authentication data.
│   │   │   │   ├── cache.py    # Redis-backed cache for refresh tokens.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for users, tokens, and auth entities.
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository.
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository.
│   │   │   ├── billing/        # Persistence implementations for billing data.
│   │   │   │   ├── __init__.py # Exposes billing repository implementations.
│   │   │   │   ├── in_memory.py # In-memory billing repository for testing and development.
│   │   │   │   └── postgres.py # Postgres-backed implementation of the billing repository.
│   │   │   ├── conversations/  # Persistence implementations for conversation data.
│   │   │   │   ├── __init__.py # Exposes conversation repository implementations.
│   │   │   │   ├── in_memory.py # In-memory conversation repository for testing/development.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for conversations, tenants, and billing.
│   │   │   │   └── postgres.py # Postgres-backed implementation of the conversation repository.
│   │   │   └── models/         # Shared base for SQLAlchemy ORM models.
│   │   │       └── base.py     # Defines the SQLAlchemy declarative base and helper functions.
│   │   └── security/           # Concrete implementations for security infrastructure.
│   │       ├── nonce_store.py  # Replay-protection store for Vault-signed requests.
│   │       ├── vault.py        # Client for HashiCorp Vault's Transit signing/verification engine.
│   │       └── vault_kv.py     # Client for HashiCorp Vault's KV secret store.
│   ├── middleware/             # Custom FastAPI middleware.
│   │   ├── __init__.py         # Initializes the 'middleware' package.
│   │   └── logging.py          # Middleware for logging HTTP requests and responses.
│   ├── observability/          # Helpers for logging, metrics, and tracing.
│   │   ├── __init__.py         # Initializes the 'observability' package.
│   │   ├── logging.py          # Structured logging helper for key application events.
│   │   └── metrics.py          # Defines and configures Prometheus metrics.
│   ├── presentation/           # Non-API, user-facing endpoints (health, metrics).
│   │   ├── __init__.py         # Initializes the 'presentation' package.
│   │   ├── health.py           # Defines /health and /health/ready endpoints.
│   │   ├── metrics.py          # Defines the /metrics endpoint for Prometheus scraping.
│   │   └── well_known.py       # Defines the /.well-known/jwks.json endpoint for JWT public keys.
│   ├── services/               # Application service layer coordinating domain and infrastructure.
│   │   ├── __init__.py         # Initializes the 'services' package.
│   │   ├── agent_service.py    # Orchestrates agent interactions, chat, and conversation state.
│   │   ├── auth_service.py     # Orchestrates user and service account authentication logic.
│   │   ├── billing_service.py  # Orchestrates billing and subscription logic.
│   │   ├── conversation_service.py # High-level service for managing conversation data.
│   │   ├── payment_gateway.py  # Abstract interface for payment providers like Stripe.
│   │   └── user_service.py     # High-level service for user registration and authentication logic.
│   └── utils/                  # General utility functions and helpers.
│       ├── __init__.py         # Initializes the 'utils' package.
│       └── tools/              # Agent tool definitions and management.
│           ├── __init__.py     # Exposes the tool registry and core tools.
│           ├── registry.py     # Central registry for managing and discovering agent tools.
│           └── web_search.py   # Defines the Tavily web search tool for agents.
├── main.py                     # Main FastAPI application entry point and configuration.
└── tests/                      # Contains all automated tests for the application.
    ├── __init__.py             # Initializes the tests package.
    ├── conftest.py             # Shared pytest fixtures for the test suite.
    ├── contract/               # Tests for the application's external API boundaries.
    │   ├── test_agents_api.py  # Contract tests for agent-related API endpoints.
    │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance.
    │   ├── test_auth_users.py  # Contract tests for user authentication API endpoints.
    │   ├── test_health_endpoints.py # Contract tests for health check endpoints.
    │   ├── test_metrics_endpoint.py # Contract tests for the Prometheus metrics endpoint.
    │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming chat.
    │   └── test_well_known.py  # Contract tests for the JWKS endpoint.
    ├── fixtures/               # Contains static data files for tests.
    │   └── keysets             # Contains test cryptographic keyset files.
    ├── integration/            # Tests requiring external services like a database.
    │   ├── __init__.py         # Initializes the integration tests package.
    │   └── test_postgres_migrations.py # Integration tests for Alembic migrations and Postgres repositories.
    └── unit/                   # Fast, isolated tests for individual components.
        ├── test_auth_domain.py # Unit tests for authentication domain helpers.
        ├── test_auth_service.py # Unit tests for the authentication service logic.
        ├── test_billing_service.py # Unit tests for the billing service.
        ├── test_config.py      # Unit tests for application configuration settings.
        ├── test_keys.py        # Unit tests for cryptographic key management logic.
        ├── test_keys_cli.py    # Unit tests for the key management CLI commands.
        ├── test_metrics.py     # Unit tests for Prometheus metrics helpers.
        ├── test_nonce_store.py # Unit tests for the nonce store for replay protection.
        ├── test_refresh_token_repository.py # Unit tests for refresh token persistence logic.
        ├── test_security.py    # Unit tests for JWT signing, verification, and password hashing.
        ├── test_tools.py       # Unit tests for the agent tool registry and definitions.
        ├── test_user_models.py # Unit tests for user-related SQLAlchemy ORM models.
        ├── test_user_repository.py # Unit tests for the user repository implementation.
        ├── test_user_service.py # Unit tests for the user service logic.
        ├── test_vault_client.py # Unit tests for the Vault Transit client.
        └── test_vault_kv.py    # Unit tests for the Vault KV secret manager client.