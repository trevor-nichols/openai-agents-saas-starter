.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                  # Alembic's runtime environment configuration for migrations.
│   └── script.py.mako          # Template for generating new Alembic migration scripts.
├── alembic.ini                 # Configuration file for the Alembic database migration tool.
├── app/                        # Main application source code directory.
│   ├── __init__.py             # Initializes the 'app' package.
│   ├── api/                    # Contains the FastAPI API layer, including routers, dependencies, and models.
│   │   ├── __init__.py         # Initializes the `api` package.
│   │   ├── dependencies/       # Reusable FastAPI dependency injection functions.
│   │   │   ├── __init__.py     # Exposes shared dependency helpers.
│   │   │   ├── auth.py         # Authentication-related dependencies (e.g., `require_current_user`).
│   │   │   ├── common.py       # Common dependencies like pagination parameters.
│   │   │   └── tenant.py       # Dependencies for handling multi-tenancy context.
│   │   ├── errors.py           # Centralized exception handlers for the API.
│   │   ├── models/             # Pydantic models for API request/response validation.
│   │   │   ├── __init__.py     # Initializes the `models` package.
│   │   │   ├── auth.py         # Pydantic models for authentication requests and responses.
│   │   │   └── common.py       # Common API models like `ErrorResponse`, `PaginatedResponse`.
│   │   ├── router.py           # Top-level API router that aggregates versioned routers.
│   │   └── v1/                 # Contains the version 1 API endpoints.
│   │       ├── __init__.py     # Initializes the `v1` package.
│   │       ├── agents/         # Endpoints related to managing and listing agents.
│   │       │   ├── __init__.py # Initializes the `agents` package.
│   │       │   ├── router.py   # FastAPI router for `/agents` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for agent-related API responses.
│   │       ├── auth/           # Endpoints for user and service account authentication.
│   │       │   ├── __init__.py # Initializes the `auth` package.
│   │       │   └── router.py   # FastAPI router for `/auth` endpoints (login, refresh, etc.).
│   │       ├── billing/        # Endpoints for managing billing and subscriptions.
│   │       │   ├── __init__.py # Initializes the `billing` package.
│   │       │   ├── router.py   # FastAPI router for `/billing` endpoints (plans, subscriptions).
│   │       │   └── schemas.py  # Pydantic schemas for billing-related API requests/responses.
│   │       ├── chat/           # Endpoints for interacting with agents via chat.
│   │       │   ├── __init__.py # Initializes the `chat` package.
│   │       │   ├── router.py   # FastAPI router for `/chat` and `/chat/stream` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for chat requests and responses.
│   │       ├── conversations/  # Endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the `conversations` package.
│   │       │   ├── router.py   # FastAPI router for `/conversations` endpoints.
│   │       │   └── schemas.py  # Pydantic schemas for conversation history and summaries.
│   │       ├── router.py       # Aggregates all v1 API routers.
│   │       └── tools/          # Endpoints for inspecting available agent tools.
│   │           ├── __init__.py # Initializes the `tools` package.
│   │           └── router.py   # FastAPI router for `/tools` endpoint.
│   ├── cli/                    # Command-line interface tools for the application.
│   │   ├── __init__.py         # Initializes the `cli` package.
│   │   └── auth_cli.py         # CLI for authentication tasks like issuing service account tokens.
│   ├── core/                   # Core application logic, configuration, and security primitives.
│   │   ├── __init__.py         # Initializes the `core` package.
│   │   ├── config.py           # Pydantic-based settings management from environment variables.
│   │   ├── keys.py             # Manages cryptographic keys (Ed25519) for JWT signing.
│   │   ├── security.py         # Handles JWT creation, verification, and password hashing.
│   │   ├── service_accounts.py # Loads and manages service account definitions from YAML.
│   │   └── service_accounts.yaml # YAML configuration file defining available service accounts.
│   ├── domain/                 # Defines core business logic, models, and repository interfaces (contracts).
│   │   ├── __init__.py         # Initializes the `domain` package.
│   │   ├── auth.py             # Domain models and repository protocol for authentication tokens.
│   │   ├── billing.py          # Domain models and repository protocol for billing.
│   │   ├── conversations.py    # Domain models and repository protocol for conversations.
│   │   └── users.py            # Domain models and repository protocol for human users.
│   ├── infrastructure/         # Implementation of external concerns like databases and third-party APIs.
│   │   ├── __init__.py         # Initializes the `infrastructure` package.
│   │   ├── db/                 # Database connection and session management.
│   │   │   ├── __init__.py     # Exposes key database helpers.
│   │   │   ├── engine.py       # Manages the SQLAlchemy async engine and migrations.
│   │   │   └── session.py      # FastAPI dependency for getting a DB session.
│   │   ├── openai/             # Wrappers and configuration for the OpenAI/Agents SDK.
│   │   │   ├── __init__.py     # Initializes the `openai` package.
│   │   │   ├── runner.py       # Wrapper for executing agents via the SDK's `Runner`.
│   │   │   └── sessions.py     # Manages SQLAlchemy-backed sessions for the Agents SDK.
│   │   ├── persistence/        # Concrete implementations of the domain repository interfaces.
│   │   │   ├── __init__.py     # Initializes the `persistence` package.
│   │   │   ├── auth/           # Persistence for authentication-related data.
│   │   │   │   ├── cache.py    # Redis-based cache for refresh tokens.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for users, tokens, and auth entities.
│   │   │   │   ├── repository.py # Postgres implementation of the `RefreshTokenRepository`.
│   │   │   │   └── user_repository.py # Postgres implementation of the `UserRepository`.
│   │   │   ├── billing/        # Persistence for billing data.
│   │   │   │   ├── __init__.py # Exposes the postgres billing repository.
│   │   │   │   └── postgres.py # Postgres implementation of the `BillingRepository`.
│   │   │   ├── conversations/  # Persistence for conversation data.
│   │   │   │   ├── __init__.py # Exposes the postgres conversation repository.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for conversations, tenants, and billing.
│   │   │   │   └── postgres.py # Postgres implementation of the `ConversationRepository`.
│   │   │   ├── models/         # Base models for persistence layer.
│   │   │   │   └── base.py     # Shared SQLAlchemy declarative base.
│   │   │   └── stripe/         # Persistence for Stripe-related data.
│   │   │       ├── models.py   # SQLAlchemy ORM models for Stripe events.
│   │   │       └── repository.py # Repository for storing and retrieving Stripe webhook events.
│   │   ├── security/           # Security-related infrastructure implementations.
│   │   │   ├── nonce_store.py  # Redis-based store for preventing replay attacks.
│   │   │   ├── vault.py        # Client for interacting with HashiCorp Vault's Transit engine.
│   │   │   └── vault_kv.py     # Client for interacting with HashiCorp Vault's KV store.
│   │   └── stripe/             # Client for interacting with the Stripe API.
│   │       ├── __init__.py     # Exposes the Stripe client components.
│   │       └── client.py       # Typed wrapper around the Stripe Python library with retries.
│   ├── middleware/             # Custom FastAPI/Starlette middleware.
│   │   ├── __init__.py         # Initializes the `middleware` package.
│   │   └── logging.py          # Middleware for request/response logging with correlation IDs.
│   ├── observability/          # Code for logging, metrics, and tracing.
│   │   ├── __init__.py         # Initializes the `observability` package.
│   │   ├── logging.py          # Structured logging helper functions.
│   │   └── metrics.py          # Prometheus metrics definitions and collectors.
│   ├── presentation/           # Non-API endpoints like health checks and webhooks.
│   │   ├── __init__.py         # Initializes the `presentation` package.
│   │   ├── health.py           # Liveness and readiness probe endpoints.
│   │   ├── metrics.py          # Prometheus metrics scrape endpoint.
│   │   ├── webhooks/           # Handlers for incoming webhooks from external services.
│   │   │   ├── __init__.py     # Initializes the `webhooks` package.
│   │   │   └── stripe.py       # Webhook handler for Stripe events.
│   │   └── well_known.py       # Endpoints for `.well-known` URIs like `jwks.json`.
│   ├── services/               # Business logic services that orchestrate domain objects and repositories.
│   │   ├── __init__.py         # Initializes the `services` package.
│   │   ├── agent_service.py    # Core service for orchestrating agent interactions and managing conversations.
│   │   ├── auth_service.py     # Service for handling user and service account authentication logic.
│   │   ├── billing_events.py   # Service for broadcasting and streaming billing events via Redis.
│   │   ├── billing_service.py  # Service for managing subscriptions and billing plans.
│   │   ├── conversation_service.py # Service for managing conversation history persistence.
│   │   ├── payment_gateway.py  # Abstraction layer for payment providers like Stripe.
│   │   ├── stripe_dispatcher.py # Service for dispatching Stripe webhook events to handlers.
│   │   ├── stripe_retry_worker.py # Background task that replays failed Stripe dispatch rows on a schedule.
│   │   └── user_service.py     # Service for managing human user accounts, authentication, and lockouts.
│   └── utils/                  # General utility functions and classes.
│       ├── __init__.py         # Initializes the `utils` package.
│       └── tools/              # Agent tool definitions and registry.
│           ├── __init__.py     # Exposes tool components.
│           ├── registry.py     # Central registry for managing agent tools.
│           └── web_search.py   # Defines a web search tool using the Tavily API.
├── main.py                     # The main entry point for the FastAPI application.
├── tests/                      # Contains all automated tests for the application.
│   ├── __init__.py             # Initializes the `tests` package.
│   ├── conftest.py             # Shared pytest fixtures and configuration for tests.
│   ├── contract/               # Tests for the application's external contracts (APIs).
│   │   ├── test_agents_api.py  # Contract tests for the agent and chat APIs.
│   │   ├── test_auth_service_accounts.py # Contract tests for service account authentication via CLI.
│   │   ├── test_auth_users.py  # Contract tests for human user authentication endpoints.
│   │   ├── test_health_endpoints.py # Contract tests for health and readiness endpoints.
│   │   ├── test_metrics_endpoint.py # Contract test for the Prometheus metrics endpoint.
│   │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming.
│   │   └── test_well_known.py  # Contract tests for the `.well-known/jwks.json` endpoint.
│   ├── fixtures/               # Test data fixtures.
│   │   ├── keysets/            # Contains test cryptographic keyset files.
│   │   └── stripe/             # Contains Stripe webhook event fixture files.
│   ├── integration/            # Tests that require external services like a real database.
│   │   ├── __init__.py         # Initializes the `integration` test package.
│   │   ├── test_billing_stream.py # Integration test for the billing SSE stream.
│   │   ├── test_postgres_migrations.py # Integration tests for Alembic migrations and repositories.
│   │   └── test_stripe_webhook.py # Integration test for the Stripe webhook endpoint.
│   ├── unit/                   # Fast tests with mocked or in-memory dependencies.
│   │   ├── test_auth_domain.py # Unit tests for authentication domain logic.
│   │   ├── test_auth_service.py # Unit tests for the authentication service.
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic.
│   │   ├── test_billing_events.py # Unit tests for the billing events service.
│   │   ├── test_billing_service.py # Unit tests for the billing service.
│   │   ├── test_config.py      # Unit tests for application settings validation.
│   │   ├── test_keys.py        # Unit tests for cryptographic key management.
│   │   ├── test_keys_cli.py    # Unit tests for the key management CLI.
│   │   ├── test_metrics.py     # Unit tests for Prometheus metrics helpers.
│   │   ├── test_nonce_store.py # Unit tests for the nonce store for replay protection.
│   │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository logic.
│   │   ├── test_security.py    # Unit tests for security utilities (JWT, password hashing).
│   │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher.
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
│   │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry worker.
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│   │   ├── test_tools.py       # Unit tests for agent tools and registry.
│   │   ├── test_user_models.py # Unit tests for user-related ORM models.
│   │   ├── test_user_repository.py # Unit tests for the user repository.
│   │   ├── test_user_service.py # Unit tests for the user service.
│   │   ├── test_vault_client.py # Unit tests for the Vault Transit client.
│   │   └── test_vault_kv.py    # Unit tests for the Vault KV client.
│   └── utils/                  # Utility code specifically for tests.
│       └── fake_billing_backend.py # A fake, in-memory billing event backend for testing.
└── var/                        # Directory for variable data, like keys.
    └── keys/                   # Default location for storing cryptographic keys on the filesystem.
