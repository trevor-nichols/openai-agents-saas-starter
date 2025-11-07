.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                  # Alembic runtime environment configuration for applying migrations.
│   └── script.py.mako          # Mako template for generating new Alembic migration scripts.
├── alembic.ini                 # Configuration file for Alembic database migrations.
├── app/                        # Main application source code directory.
│   ├── __init__.py             # Initializes the `app` package.
│   ├── api/                    # Contains the FastAPI API layer, including routers, schemas, and dependencies.
│   │   ├── __init__.py         # Initializes the `api` package.
│   │   ├── dependencies/       # Houses reusable FastAPI dependency injections.
│   │   │   ├── __init__.py     # Exposes shared dependency helpers for convenient import.
│   │   │   ├── auth.py         # Authentication dependency to get the current authenticated user.
│   │   │   ├── common.py       # Common dependencies like pagination parameter handling.
│   │   │   └── tenant.py       # Dependencies for multi-tenant context and role checking.
│   │   ├── errors.py           # Centralized API exception handlers for consistent error responses.
│   │   ├── models/             # Pydantic models for API requests and responses (schemas).
│   │   │   ├── __init__.py     # Initializes the `models` package.
│   │   │   ├── auth.py         # Pydantic models for authentication requests and responses.
│   │   │   └── common.py       # Common Pydantic models like SuccessResponse and ErrorResponse.
│   │   ├── router.py           # Top-level API router that aggregates versioned routers.
│   │   └── v1/                 # Contains all components for the v1 API.
│   │       ├── __init__.py     # Initializes the `v1` API package.
│   │       ├── agents/         # Endpoints related to the agent catalog and status.
│   │       │   ├── __init__.py # Initializes the `agents` API package.
│   │       │   ├── router.py   # FastAPI router for `/api/v1/agents` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for agent-related API responses.
│   │       ├── auth/           # Endpoints for user and service account authentication.
│   │       │   ├── __init__.py # Initializes the `auth` API package.
│   │       │   └── router.py   # FastAPI router for `/api/v1/auth` endpoints (login, refresh, etc.).
│   │       ├── billing/        # Endpoints for managing billing and subscriptions.
│   │       │   ├── __init__.py # Initializes the `billing` API package.
│   │       │   ├── router.py   # FastAPI router for `/api/v1/billing` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for billing-related API requests and responses.
│   │       ├── chat/           # Endpoints for chat interactions with agents.
│   │       │   ├── __init__.py # Initializes the `chat` API package.
│   │       │   ├── router.py   # FastAPI router for `/api/v1/chat` endpoints, including streaming.
│   │       │   └── schemas.py  # Pydantic schemas for chat requests and responses.
│   │       ├── conversations/  # Endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the `conversations` API package.
│   │       │   ├── router.py   # FastAPI router for `/api/v1/conversations` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for conversation history and summaries.
│   │       ├── router.py       # Aggregates all v1 API routers into a single router.
│   │       └── tools/          # Endpoint for listing available agent tools.
│   │           ├── __init__.py # Initializes the `tools` API package.
│   │           └── router.py   # FastAPI router for the `/api/v1/tools` endpoint.
│   ├── cli/                    # Command-line interface utilities.
│   │   ├── __init__.py         # Initializes the `cli` package.
│   │   └── auth_cli.py         # CLI for auth tasks like issuing service account tokens and managing keys.
│   ├── core/                   # Core application logic, configuration, and security.
│   │   ├── __init__.py         # Initializes the `core` package.
│   │   ├── config.py           # Pydantic-based settings management from environment variables.
│   │   ├── keys.py             # Ed25519 key generation, storage, and JWKS management.
│   │   ├── security.py         # JWT, password hashing, and token signing/verification logic.
│   │   ├── service_accounts.py # Loads and manages service account definitions from YAML.
│   │   └── service_accounts.yaml # YAML definitions for available service accounts.
│   ├── domain/                 # Core business logic, entities, and repository interfaces (protocols).
│   │   ├── __init__.py         # Initializes the `domain` package.
│   │   ├── auth.py             # Domain models and repository protocol for authentication tokens.
│   │   ├── billing.py          # Domain models and repository protocol for billing.
│   │   ├── conversations.py    # Domain models and repository protocol for conversations.
│   │   └── users.py            # Domain models and repository protocol for human users.
│   ├── infrastructure/         # Adapters for external systems like databases and third-party APIs.
│   │   ├── __init__.py         # Initializes the `infrastructure` package.
│   │   ├── db/                 # Database connection management using SQLAlchemy.
│   │   │   ├── __init__.py     # Exposes key database functions for easy import.
│   │   │   ├── engine.py       # Manages the async SQLAlchemy engine, sessions, and migrations.
│   │   │   └── session.py      # FastAPI dependency for providing database sessions to endpoints.
│   │   ├── openai/             # Wrappers for OpenAI-related SDKs.
│   │   │   ├── __init__.py     # Initializes the `openai` package.
│   │   │   └── runner.py       # Wrapper around the OpenAI Agents SDK runner.
│   │   ├── persistence/        # Data persistence implementations (repositories).
│   │   │   ├── __init__.py     # Initializes the `persistence` package.
│   │   │   ├── auth/           # Persistence implementations for authentication data.
│   │   │   │   ├── cache.py    # Redis cache implementation for refresh tokens.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for users, tenants, and auth tokens.
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository.
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository.
│   │   │   ├── billing/        # Persistence implementations for billing data.
│   │   │   │   ├── __init__.py # Exposes billing repository implementations.
│   │   │   │   ├── in_memory.py # In-memory implementation of the billing repository for tests/dev.
│   │   │   │   └── postgres.py # Postgres implementation of the billing repository.
│   │   │   ├── conversations/  # Persistence implementations for conversation data.
│   │   │   │   ├── __init__.py # Exposes conversation repository implementations.
│   │   │   │   ├── in_memory.py # In-memory implementation of the conversation repository.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for conversations, tenants, and billing.
│   │   │   │   └── postgres.py # Postgres implementation of the conversation repository.
│   │   │   ├── models/         # Shared persistence components.
│   │   │   │   └── base.py     # SQLAlchemy declarative base and helper functions.
│   │   │   └── stripe/         # Persistence related to Stripe.
│   │   │       ├── models.py   # SQLAlchemy ORM model for storing Stripe webhook events.
│   │   │       └── repository.py # Repository for storing and retrieving Stripe webhook events.
│   │   ├── security/           # Security-related infrastructure adapters.
│   │   │   ├── nonce_store.py  # Anti-replay nonce store for Vault-signed requests.
│   │   │   ├── vault.py        # Client for HashiCorp Vault's transit engine.
│   │   │   └── vault_kv.py     # Client for HashiCorp Vault's KV secret store.
│   │   └── stripe/             # Adapters for the Stripe API.
│   │       ├── __init__.py     # Exposes the Stripe client.
│   │       └── client.py       # A typed, async-friendly client wrapper for the Stripe API.
│   ├── middleware/             # Custom FastAPI middleware.
│   │   ├── __init__.py         # Initializes the `middleware` package.
│   │   └── logging.py          # Middleware for logging HTTP requests and responses.
│   ├── observability/          # Code for logging, metrics, and tracing.
│   │   ├── __init__.py         # Initializes the `observability` package.
│   │   ├── logging.py          # Structured logging helper functions.
│   │   └── metrics.py          # Prometheus metrics definitions and helpers.
│   ├── presentation/           # Root-level, non-versioned API endpoints.
│   │   ├── __init__.py         # Initializes the `presentation` package.
│   │   ├── health.py           # Health and readiness check endpoints.
│   │   ├── metrics.py          # Endpoint for exposing Prometheus metrics.
│   │   ├── webhooks/           # Inbound webhook handlers.
│   │   │   ├── __init__.py     # Initializes the `webhooks` package.
│   │   │   └── stripe.py       # Webhook handler for Stripe events.
│   │   └── well_known.py       # Endpoints for `.well-known` URIs, like JWKS.
│   ├── services/               # Business logic and orchestration layer.
│   │   ├── __init__.py         # Initializes the `services` package.
│   │   ├── agent_service.py    # Core service for orchestrating agent interactions.
│   │   ├── auth_service.py     # Service for user and service account authentication logic.
│   │   ├── billing_events.py   # Service for broadcasting and replaying billing events.
│   │   ├── billing_service.py  # Service for managing subscriptions and billing plans.
│   │   ├── conversation_service.py # Service for managing conversation history.
│   │   ├── payment_gateway.py  # Abstraction for payment providers like Stripe.
│   │   └── user_service.py     # Service for managing human user accounts.
│   └── utils/                  # General utility functions and helpers.
│       ├── __init__.py         # Initializes the `utils` package.
│       └── tools/              # Agent tool definitions and registry.
│           ├── __init__.py     # Exposes tool registry components.
│           ├── registry.py     # Central registry for managing agent tools.
│           └── web_search.py   # Defines a web search tool using the Tavily API.
├── main.py                     # Main FastAPI application entry point and configuration.
├── tests/                      # Test suite for the application.
│   ├── __init__.py             # Initializes the `tests` package.
│   ├── conftest.py             # Shared pytest fixtures for the test suite.
│   ├── contract/               # Tests for API boundaries and external contracts.
│   │   ├── test_agents_api.py  # Contract tests for agent-related API endpoints.
│   │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance.
│   │   ├── test_auth_users.py  # Contract tests for human user authentication endpoints.
│   │   ├── test_health_endpoints.py # Contract tests for health and readiness endpoints.
│   │   ├── test_metrics_endpoint.py # Contract tests for the Prometheus metrics endpoint.
│   │   ├── test_streaming_manual.py # Manual test script for streaming chat endpoint.
│   │   └── test_well_known.py  # Contract tests for the JWKS endpoint.
│   ├── fixtures/               # Test data and fixture files.
│   │   ├── keysets/            # Contains test keyset files.
│   │   └── stripe/             # Contains Stripe webhook event fixture files.
│   ├── integration/            # Tests requiring external services like a database.
│   │   ├── __init__.py         # Initializes the `integration` test package.
│   │   ├── test_billing_stream.py # Integration tests for the SSE billing event stream.
│   │   ├── test_postgres_migrations.py # Integration tests for Alembic migrations and repositories.
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook handler.
│   └── unit/                   # Fast, isolated unit tests.
│       ├── test_auth_domain.py # Unit tests for auth domain helpers.
│       ├── test_auth_service.py # Unit tests for the authentication service logic.
│       ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation.
│       ├── test_billing_events.py # Unit tests for the billing events service.
│       ├── test_billing_service.py # Unit tests for the billing service logic.
│       ├── test_config.py      # Unit tests for application settings validation.
│       ├── test_keys.py        # Unit tests for cryptographic key management.
│       ├── test_keys_cli.py    # Unit tests for the key management CLI.
│       ├── test_metrics.py     # Unit tests for Prometheus metrics helpers.
│       ├── test_nonce_store.py # Unit tests for the anti-replay nonce store.
│       ├── test_refresh_token_repository.py # Unit tests for the refresh token repository logic.
│       ├── test_security.py    # Unit tests for JWT and password security functions.
│       ├── test_stripe_events.py # Unit tests for the Stripe event repository.
│       ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│       ├── test_tools.py       # Unit tests for the agent tool registry.
│       ├── test_user_models.py # Unit tests for user-related SQLAlchemy models.
│       ├── test_user_repository.py # Unit tests for the user repository implementation.
│       ├── test_user_service.py # Unit tests for the user service logic.
│       ├── test_vault_client.py # Unit tests for the Vault Transit client.
│       └── test_vault_kv.py    # Unit tests for the Vault KV secret store client.
└── var/                        # Directory for variable data like keys.
    └── keys/                   # Default location for storing cryptographic keys on disk.