.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                 # Alembic environment script for running migrations, configured for async.
│   └── script.py.mako         # Template for generating new Alembic migration scripts.
├── alembic.ini                 # Configuration file for the Alembic database migration tool.
├── app/                        # Main application source code directory.
│   ├── __init__.py            # Initializes the `app` package.
│   ├── api/                     # Contains the FastAPI API layer, including routers, dependencies, and models.
│   │   ├── __init__.py          # Initializes the `api` package.
│   │   ├── dependencies/        # FastAPI dependency injection helpers for routers.
│   │   │   ├── __init__.py      # Exposes shared dependency helpers.
│   │   │   ├── auth.py          # Authentication and authorization dependencies (e.g., `require_scopes`).
│   │   │   ├── common.py        # Common API dependencies like pagination.
│   │   │   ├── rate_limit.py    # Helper to translate rate limit errors into HTTP 429 responses.
│   │   │   └── tenant.py        # Dependencies for multi-tenancy context and role enforcement.
│   │   ├── errors.py            # Centralized exception handlers for the API.
│   │   ├── models/              # Pydantic models for API request/response bodies.
│   │   │   ├── __init__.py      # Initializes the `models` package.
│   │   │   ├── auth.py          # Pydantic models for authentication requests and responses.
│   │   │   └── common.py        # Common API models like `SuccessResponse` and `ErrorResponse`.
│   │   ├── router.py            # Top-level API router that includes versioned routers.
│   │   └── v1/                  # Contains the version 1 API endpoints.
│   │       ├── __init__.py      # Initializes the `v1` API package.
│   │       ├── agents/          # API endpoints for managing and querying agents.
│   │       │   ├── __init__.py  # Initializes the `agents` package.
│   │       │   ├── router.py    # FastAPI router for agent catalog endpoints.
│   │       │   └── schemas.py   # Pydantic schemas for agent-related API responses.
│   │       ├── auth/            # API endpoints for user and service account authentication.
│   │       │   ├── __init__.py  # Initializes the `auth` package.
│   │       │   └── router.py    # FastAPI router for authentication endpoints (login, register, refresh).
│   │       ├── billing/         # API endpoints for billing and subscription management.
│   │       │   ├── __init__.py  # Initializes the `billing` API package.
│   │       │   ├── router.py    # FastAPI router for billing endpoints (plans, subscriptions, usage).
│   │       │   └── schemas.py   # Pydantic schemas for billing API requests and responses.
│   │       ├── chat/            # API endpoints for interacting with agents.
│   │       │   ├── __init__.py  # Initializes the `chat` package.
│   │       │   ├── router.py    # FastAPI router for chat and streaming chat endpoints.
│   │       │   └── schemas.py   # Pydantic schemas for chat requests and responses.
│   │       ├── conversations/   # API endpoints for managing conversation history.
│   │       │   ├── __init__.py  # Initializes the `conversations` package.
│   │       │   ├── router.py    # FastAPI router for conversation history management (list, get, delete).
│   │       │   └── schemas.py   # Pydantic schemas for conversation history resources.
│   │       ├── router.py        # Aggregates all routers for the v1 API.
│   │       └── tools/           # API endpoints for inspecting available tools.
│   │           ├── __init__.py  # Initializes the `tools` package.
│   │           └── router.py    # FastAPI router for listing available agent tools.
│   ├── cli/                     # Command-line interface scripts for the application.
│   │   ├── __init__.py          # Initializes the `cli` package.
│   │   └── auth_cli.py          # CLI for authentication tasks like issuing service account tokens and key management.
│   ├── core/                    # Core application logic, configuration, and security components.
│   │   ├── __init__.py          # Initializes the `core` package.
│   │   ├── config.py            # Pydantic-based application settings management.
│   │   ├── keys.py              # Ed25519 key generation, storage, and management for JWT signing.
│   │   ├── password_policy.py   # Centralized password strength validation logic.
│   │   ├── security.py          # JWT, password hashing, and token signing/verification utilities.
│   │   ├── service_accounts.py  # Loads and manages service account definitions from YAML.
│   │   └── service_accounts.yaml # YAML file defining available service accounts and their permissions.
│   ├── domain/                  # Defines core business models (entities) and repository interfaces (contracts).
│   │   ├── __init__.py          # Initializes the `domain` package.
│   │   ├── auth.py              # Domain models and repository protocol for authentication tokens.
│   │   ├── billing.py           # Domain models and repository protocol for billing and subscriptions.
│   │   ├── conversations.py     # Domain models and repository protocol for conversations.
│   │   └── users.py             # Domain models and repository protocol for user accounts.
│   ├── infrastructure/          # Implementation of external-facing components like databases and APIs.
│   │   ├── __init__.py          # Initializes the `infrastructure` package.
│   │   ├── db/                  # Database connection and session management.
│   │   │   ├── __init__.py      # Exposes key database management functions.
│   │   │   ├── engine.py        # Manages the global SQLAlchemy async engine and session factory.
│   │   │   └── session.py       # FastAPI dependency for obtaining a database session.
│   │   ├── openai/              # Integration with the OpenAI Agents SDK.
│   │   │   ├── __init__.py      # Initializes the `openai` infrastructure package.
│   │   │   ├── runner.py        # Wrappers around the OpenAI Agents SDK runner.
│   │   │   └── sessions.py      # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/         # Concrete implementations of the domain repository protocols.
│   │   │   ├── __init__.py      # Initializes the `persistence` package.
│   │   │   ├── auth/            # Persistence logic for authentication-related data.
│   │   │   │   ├── cache.py     # Redis-backed cache for refresh tokens.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for users, tenants, and tokens.
│   │   │   │   ├── repository.py # Postgres implementation of the RefreshTokenRepository.
│   │   │   │   └── user_repository.py # Postgres implementation of the UserRepository.
│   │   │   ├── billing/         # Persistence logic for billing data.
│   │   │   │   ├── __init__.py  # Initializes the `billing` persistence package.
│   │   │   │   └── postgres.py  # Postgres implementation of the BillingRepository.
│   │   │   ├── conversations/   # Persistence logic for conversation data.
│   │   │   │   ├── __init__.py  # Initializes the `conversations` persistence package.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for conversations, tenants, and billing entities.
│   │   │   │   └── postgres.py  # Postgres implementation of the ConversationRepository.
│   │   │   ├── models/          # Base models for persistence layer.
│   │   │   │   └── base.py      # Shared SQLAlchemy declarative base and helper functions.
│   │   │   ├── stripe/          # Persistence logic for Stripe webhook events.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for Stripe events and dispatches.
│   │   │   │   └── repository.py # Implements storage and retrieval for Stripe events.
│   │   │   └── tenants/         # (Empty) Directory for tenant-related persistence.
│   │   ├── security/            # Security-related infrastructure implementations.
│   │   │   ├── nonce_store.py   # Redis-based store for nonce replay protection.
│   │   │   ├── vault.py         # Client for HashiCorp Vault's Transit secret engine.
│   │   │   └── vault_kv.py      # Client for HashiCorp Vault's KV secret engine.
│   │   └── stripe/              # Client and type definitions for interacting with the Stripe API.
│   │       ├── __init__.py      # Initializes the Stripe client package.
│   │       ├── client.py        # A typed client wrapper for the Stripe API with retries.
│   │       └── types.py         # Typing helpers and wrappers for the dynamic Stripe SDK.
│   ├── middleware/              # Custom FastAPI middleware.
│   │   ├── __init__.py          # Initializes the `middleware` package.
│   │   └── logging.py           # Middleware for request/response logging with correlation IDs.
│   ├── observability/           # Helpers for logging, metrics, and tracing.
│   │   ├── __init__.py          # Initializes the `observability` package.
│   │   ├── logging.py           # Structured logging helper for application events.
│   │   └── metrics.py           # Prometheus metrics definitions and helpers.
│   ├── presentation/            # Non-API HTTP endpoints (health checks, webhooks, etc.).
│   │   ├── __init__.py          # Initializes the `presentation` package.
│   │   ├── health.py            # FastAPI routers for liveness and readiness health checks.
│   │   ├── metrics.py           # FastAPI router for the Prometheus metrics scrape endpoint.
│   │   ├── webhooks/            # Endpoints for receiving webhooks from external services.
│   │   │   ├── __init__.py      # Initializes the `webhooks` package.
│   │   │   └── stripe.py        # FastAPI router for handling incoming Stripe webhooks.
│   │   └── well_known.py        # FastAPI router for /.well-known endpoints like JWKS.
│   ├── services/                # Business logic layer, orchestrating domain and infrastructure components.
│   │   ├── __init__.py          # Initializes the `services` package.
│   │   ├── agent_service.py     # Core service for orchestrating agent interactions and managing tools.
│   │   ├── auth_service.py      # Service for handling user and service account authentication logic.
│   │   ├── billing_events.py    # Service for broadcasting billing events to subscribers via Redis.
│   │   ├── billing_service.py   # Service for managing billing plans and subscriptions.
│   │   ├── conversation_service.py # Service layer for managing conversation history.
│   │   ├── payment_gateway.py   # Abstraction layer for payment providers like Stripe.
│   │   ├── rate_limit_service.py # Redis-backed service for API rate limiting.
│   │   ├── signup_service.py    # Service orchestrating the user/tenant self-serve registration process.
│   │   ├── stripe_dispatcher.py # Service for routing Stripe webhook events to appropriate handlers.
│   │   ├── stripe_event_models.py # Dataclasses for Stripe webhook dispatch context and results.
│   │   ├── stripe_retry_worker.py # Background worker for retrying failed Stripe event dispatches.
│   │   └── user_service.py      # Service for managing user accounts, passwords, and lockouts.
│   └── utils/                   # General utility functions and helpers.
│       ├── __init__.py          # Initializes the `utils` package.
│       └── tools/               # Utilities related to agent tools.
│           ├── __init__.py      # Exports tool registry components.
│           ├── registry.py      # Central registry for managing and discovering agent tools.
│           └── web_search.py    # Implements a web search tool using the Tavily API.
├── main.py                     # The main FastAPI application entry point.
├── tests/                      # Directory containing all automated tests for the application.
│   ├── __init__.py            # Initializes the `tests` package.
│   ├── conftest.py              # Shared pytest fixtures and configuration for the test suite.
│   ├── contract/                # API contract tests using the FastAPI TestClient.
│   │   ├── test_agents_api.py   # Contract tests for the agent and chat API endpoints.
│   │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance.
│   │   ├── test_auth_users.py   # Contract tests for user authentication endpoints.
│   │   ├── test_health_endpoints.py # Contract tests for the `/health` and `/health/ready` endpoints.
│   │   ├── test_metrics_endpoint.py # Contract tests for the `/metrics` Prometheus endpoint.
│   │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming chat.
│   │   └── test_well_known.py   # Contract tests for the `/.well-known/jwks.json` endpoint.
│   ├── fixtures/                # Test data and fixture files.
│   │   ├── keysets/             # Contains test cryptographic key files.
│   │   └── stripe/              # Contains Stripe webhook fixture files.
│   ├── integration/             # Tests that require external resources like a database or network.
│   │   ├── __init__.py          # Initializes the `integration` test package.
│   │   ├── test_billing_stream.py # Integration tests for the server-sent events (SSE) billing stream.
│   │   ├── test_postgres_migrations.py # Integration tests to verify database migrations and repository functionality.
│   │   ├── test_stripe_replay_cli.py # Integration tests for the Stripe event replay CLI script.
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook endpoint.
│   ├── unit/                    # Fast, isolated unit tests with mocked dependencies.
│   │   ├── test_auth_domain.py  # Unit tests for authentication domain helpers.
│   │   ├── test_auth_service.py # Unit tests for the authentication service logic.
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic.
│   │   ├── test_billing_events.py # Unit tests for the billing events broadcasting service.
│   │   ├── test_billing_service.py # Unit tests for the billing service logic.
│   │   ├── test_config.py       # Unit tests for application settings parsing and validation.
│   │   ├── test_keys.py         # Unit tests for JWT key storage and management helpers.
│   │   ├── test_keys_cli.py     # Unit tests for the key management CLI commands.
│   │   ├── test_metrics.py      # Unit tests for Prometheus metrics helpers.
│   │   ├── test_nonce_store.py  # Unit tests for the nonce replay-protection store.
│   │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
│   │   ├── test_refresh_token_repository.py # Unit tests for refresh token persistence and rehydration.
│   │   ├── test_scope_dependencies.py # Unit tests for API scope dependency helpers.
│   │   ├── test_secret_guard.py # Unit tests for production secret enforcement logic.
│   │   ├── test_security.py     # Unit tests for JWT signing/verification and security dependencies.
│   │   ├── test_signup_service.py # Unit tests for the user signup service logic.
│   │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe webhook event dispatcher.
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│   │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry worker.
│   │   ├── test_tenant_dependency.py # Unit tests for the multi-tenancy context dependency.
│   │   ├── test_tools.py        # Unit tests for the agent tool registry and tools.
│   │   ├── test_user_models.py  # Unit tests for user-related ORM model definitions.
│   │   ├── test_user_repository.py # Unit tests for the user repository implementation.
│   │   ├── test_user_service.py # Unit tests for the user management service.
│   │   ├── test_vault_client.py # Unit tests for the Vault Transit client.
│   │   └── test_vault_kv.py     # Unit tests for the Vault KV client.
│   └── utils/                   # Utility helpers for tests.
│       ├── fake_billing_backend.py # A fake in-memory billing event backend for testing.
│       └── sqlalchemy.py      # Shared SQLAlchemy test helpers.
└── var/                        # Directory for variable data, like keys.
    └── keys/                   # Default directory for storing cryptographic keys.