```
.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                 # Alembic environment script for running database migrations.
│   └── script.py.mako         # Template for generating new Alembic migration scripts.
├── alembic.ini                  # Configuration file for Alembic database migrations.
├── app/                       # Main application source code directory.
│   ├── __init__.py            # Initializes the 'app' package.
│   ├── api/                   # Contains the FastAPI API layer, including routers, models, and dependencies.
│   │   ├── __init__.py        # Initializes the 'api' package.
│   │   ├── dependencies/      # Reusable FastAPI dependencies for endpoints.
│   │   │   ├── __init__.py    # Exposes shared dependency helpers.
│   │   │   ├── auth.py        # FastAPI dependencies for authentication and scope validation.
│   │   │   ├── common.py      # Shared dependencies like pagination parameters.
│   │   │   ├── rate_limit.py  # Helper to convert rate limit errors to HTTP 429 responses.
│   │   │   └── tenant.py      # FastAPI dependencies for multi-tenancy context and role enforcement.
│   │   ├── errors.py          # Centralized exception handlers for the FastAPI application.
│   │   ├── models/            # Pydantic models for API request and response validation.
│   │   │   ├── __init__.py    # Initializes the 'api.models' package.
│   │   │   ├── auth.py        # Pydantic models for authentication-related API requests and responses.
│   │   │   └── common.py      # Common Pydantic models for API responses (Success, Error, Pagination).
│   │   ├── router.py          # Top-level API router that includes the v1 router.
│   │   └── v1/                # Contains version 1 of the API endpoints.
│   │       ├── __init__.py    # Initializes the 'v1' API package.
│   │       ├── agents/        # API endpoints related to agents.
│   │       │   ├── __init__.py # Initializes the 'agents' API package.
│   │       │   ├── router.py  # API endpoints for listing and checking the status of agents.
│   │       │   └── schemas.py # Pydantic schemas for agent-related API endpoints.
│   │       ├── auth/          # API endpoints related to authentication and authorization.
│   │       │   ├── __init__.py # Initializes the 'auth' API package.
│   │       │   ├── router.py  # Aggregates all authentication-related API routes.
│   │       │   ├── routes_email.py # API endpoints for handling email verification.
│   │       │   ├── routes_passwords.py # API endpoints for password management (forgot, reset, change).
│   │       │   ├── routes_service_accounts.py # API endpoint for issuing service account tokens with Vault integration.
│   │       │   ├── routes_sessions.py # API endpoints for user session management (login, logout, refresh, list).
│   │       │   ├── routes_signup.py # API endpoint for public user and tenant registration.
│   │       │   └── utils.py   # Utility functions for authentication API routes.
│   │       ├── billing/       # API endpoints related to billing and subscriptions.
│   │       │   ├── __init__.py # Initializes the 'billing' API package.
│   │       │   ├── router.py  # API endpoints for managing billing, subscriptions, and usage.
│   │       │   └── schemas.py # Pydantic schemas for billing-related API endpoints.
│   │       ├── chat/          # API endpoints for chat interactions with agents.
│   │       │   ├── __init__.py # Initializes the 'chat' API package.
│   │       │   ├── router.py  # API endpoints for streaming and non-streaming chat with agents.
│   │       │   └── schemas.py # Pydantic schemas for chat request and response models.
│   │       ├── conversations/ # API endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the 'conversations' API package.
│   │       │   ├── router.py  # API endpoints for listing, retrieving, and deleting conversation history.
│   │       │   └── schemas.py # Pydantic schemas for conversation and message history.
│   │       ├── router.py      # Aggregates all v1 API routers (auth, chat, agents, etc.).
│   │       └── tools/         # API endpoints related to agent tools.
│   │           ├── __init__.py # Initializes the 'tools' API package.
│   │           └── router.py  # API endpoint for listing available agent tools.
│   ├── cli/                   # Command-line interface scripts for the application.
│   │   ├── __init__.py        # Initializes the command-line interface package.
│   │   └── auth_cli.py        # CLI for issuing service account tokens and managing signing keys.
│   ├── core/                  # Core application components like configuration and security.
│   │   ├── __init__.py        # Initializes the 'core' application package.
│   │   ├── config.py          # Defines application settings using Pydantic's `BaseSettings`.
│   │   ├── keys.py            # Manages cryptographic key lifecycle, storage, and JWKS generation.
│   │   ├── password_policy.py # Defines and validates password strength requirements.
│   │   ├── security.py        # Handles JWT creation/verification, password hashing, and auth dependencies.
│   │   ├── service_accounts.py # Loads and manages service account definitions from a YAML file.
│   │   └── service_accounts.yaml # Defines available service accounts, their scopes, and properties.
│   ├── domain/                # Contains domain models and repository contracts (protocols).
│   │   ├── __init__.py        # Initializes the 'domain' package for business models.
│   │   ├── auth.py            # Defines domain models and repository protocols for authentication.
│   │   ├── billing.py         # Defines domain models and repository protocols for billing.
│   │   ├── conversations.py   # Defines domain models and repository protocols for conversations.
│   │   ├── email_verification.py # Defines domain models for email verification tokens.
│   │   ├── password_reset.py  # Defines domain models and store protocol for password reset tokens.
│   │   └── users.py           # Defines user-related domain models and repository protocols.
│   ├── infrastructure/        # Implements interfaces to external systems (DB, APIs, etc.).
│   │   ├── __init__.py        # Initializes the 'infrastructure' package.
│   │   ├── db/                # Database connection and session management.
│   │   │   ├── __init__.py    # Exposes database engine and session management utilities.
│   │   │   ├── engine.py      # Manages the async SQLAlchemy engine and session factory lifecycle.
│   │   │   └── session.py     # FastAPI dependency for providing database sessions to endpoints.
│   │   ├── notifications/     # Adapters for sending notifications like emails.
│   │   │   ├── __init__.py    # Exposes notification adapters.
│   │   │   └── resend.py      # Adapter for sending transactional emails via the Resend API.
│   │   ├── openai/            # Wrappers and helpers for interacting with OpenAI SDKs.
│   │   │   ├── __init__.py    # Initializes the OpenAI infrastructure package.
│   │   │   ├── runner.py      # Wrapper around the OpenAI Agents SDK runner for executing agents.
│   │   │   └── sessions.py    # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/       # Data persistence implementations (repositories).
│   │   │   ├── __init__.py    # Initializes the persistence layer package.
│   │   │   ├── auth/          # Repositories for authentication-related data.
│   │   │   │   ├── cache.py   # Redis-backed cache for refresh tokens.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for users, tenants, and auth tokens.
│   │   │   │   ├── repository.py # Postgres repository for service account and user refresh tokens.
│   │   │   │   ├── session_repository.py # Postgres repository for managing user session metadata.
│   │   │   │   └── user_repository.py # Postgres repository for user accounts and related data.
│   │   │   ├── billing/       # Repositories for billing data.
│   │   │   │   ├── __init__.py # Exposes the Postgres billing repository.
│   │   │   │   └── postgres.py # Postgres implementation of the billing data repository.
│   │   │   ├── conversations/ # Repositories for conversation data.
│   │   │   │   ├── __init__.py # Exposes the Postgres conversation repository.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for conversations, tenants, and billing.
│   │   │   │   └── postgres.py # Postgres implementation of the conversation data repository.
│   │   │   ├── models/        # Base SQLAlchemy model definitions.
│   │   │   │   └── base.py    # Defines the base declarative class for all SQLAlchemy models.
│   │   │   ├── stripe/        # Persistence logic related to Stripe.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for storing Stripe webhook events.
│   │   │   │   └── repository.py # Repository for storing and managing Stripe webhook events.
│   │   │   └── tenants/       # (Empty) Potentially for tenant-specific persistence.
│   │   ├── security/          # Security-related infrastructure implementations.
│   │   │   ├── email_verification_store.py # Redis-backed store for email verification tokens.
│   │   │   ├── nonce_store.py # Redis-backed store for nonce replay protection.
│   │   │   ├── password_reset_store.py # Redis-backed store for password reset tokens.
│   │   │   ├── vault.py       # Client for HashiCorp Vault's Transit secret engine.
│   │   │   └── vault_kv.py    # Client for HashiCorp Vault's KV secret engine.
│   │   └── stripe/            # Client for interacting with the Stripe API.
│   │       ├── __init__.py    # Exposes the Stripe client and its data classes.
│   │       ├── client.py      # A typed, async-friendly wrapper for the Stripe API client.
│   │       └── types.py       # Type definitions and helpers for the dynamic Stripe SDK.
│   ├── middleware/            # Custom FastAPI middleware.
│   │   ├── __init__.py        # Initializes the 'middleware' package.
│   │   └── logging.py         # FastAPI middleware for logging requests and responses.
│   ├── observability/         # Logging, metrics, and tracing utilities.
│   │   ├── __init__.py        # Initializes the observability package.
│   │   ├── logging.py         # Provides a helper for structured, event-based logging.
│   │   └── metrics.py         # Defines and exposes Prometheus metrics for the application.
│   ├── presentation/          # Non-API HTTP endpoints like health checks and webhooks.
│   │   ├── __init__.py        # Initializes the presentation layer package.
│   │   ├── emails/            # Email template rendering logic.
│   │   │   ├── __init__.py    # Exposes email template rendering functions.
│   │   │   └── templates.py   # Renders HTML and text templates for transactional emails.
│   │   ├── health.py          # Defines `/health` and `/health/ready` endpoints.
│   │   ├── metrics.py         # Defines the `/metrics` endpoint for Prometheus scraping.
│   │   ├── webhooks/          # Webhook handlers for third-party services.
│   │   │   ├── __init__.py    # Initializes the webhooks package.
│   │   │   └── stripe.py      # Endpoint for receiving and processing Stripe webhooks.
│   │   └── well_known.py      # Defines `/.well-known/jwks.json` endpoint for public key discovery.
│   ├── services/              # Contains the application's business logic services.
│   │   ├── __init__.py        # Initializes the 'services' package.
│   │   ├── agent_service.py   # Orchestrates agent interactions, chat, and conversation management.
│   │   ├── auth/              # Specialized sub-services for authentication.
│   │   │   ├── __init__.py    # Exposes specialized authentication services and errors.
│   │   │   ├── errors.py      # Custom exception classes for authentication services.
│   │   │   ├── refresh_token_manager.py # Manages the lifecycle of refresh tokens.
│   │   │   ├── service_account_service.py # Handles service account token issuance and validation logic.
│   │   │   ├── session_service.py # Manages the lifecycle of human user sessions (login, refresh, etc.).
│   │   │   └── session_store.py # High-level service for persisting user session metadata.
│   │   ├── auth_service.py    # A facade that coordinates all authentication-related sub-services.
│   │   ├── billing_events.py  # Service for broadcasting billing events via Redis streams.
│   │   ├── billing_service.py # Service layer for managing billing plans and subscriptions.
│   │   ├── conversation_service.py # High-level service for managing conversation data.
│   │   ├── email_verification_service.py # Orchestrates the email verification flow.
│   │   ├── geoip_service.py   # A pluggable service for GeoIP lookups.
│   │   ├── password_recovery_service.py # Orchestrates the password recovery (forgot password) flow.
│   │   ├── payment_gateway.py # Defines the payment gateway protocol and its Stripe implementation.
│   │   ├── rate_limit_service.py # Provides Redis-backed rate limiting functionality.
│   │   ├── signup_service.py  # Orchestrates the user and tenant self-service registration process.
│   │   ├── stripe_dispatcher.py # Dispatches Stripe webhook events to appropriate domain handlers.
│   │   ├── stripe_event_models.py # Shared data classes for Stripe webhook processing.
│   │   ├── stripe_retry_worker.py # A background worker for retrying failed Stripe event dispatches.
│   │   └── user_service.py    # Domain service for managing user logic, including authentication.
│   └── utils/                 # General utility functions and helpers.
│       ├── __init__.py        # Initializes the 'utils' package.
│       ├── tools/             # Agent tool implementations and registry.
│       │   ├── __init__.py    # Exposes the tool registry and its initialization function.
│       │   ├── registry.py    # A central registry for managing and discovering agent tools.
│       │   └── web_search.py  # Implements a web search tool using the Tavily API.
│       └── user_agent.py      # A lightweight parser for extracting browser/OS info from User-Agent strings.
├── main.py                      # The main FastAPI application entry point and configuration.
├── tests/                     # Contains all automated tests for the application.
│   ├── __init__.py            # Initializes the 'tests' package.
│   ├── conftest.py            # Shared Pytest fixtures for the test suite.
│   ├── contract/              # API contract and boundary tests using TestClient.
│   │   ├── test_agents_api.py # Contract tests for the agent and chat API endpoints.
│   │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance.
│   │   ├── test_auth_users.py # Contract tests for human user authentication API endpoints.
│   │   ├── test_health_endpoints.py # Contract tests for the health and readiness endpoints.
│   │   ├── test_metrics_endpoint.py # Contract test for the Prometheus metrics endpoint.
│   │   ├── test_streaming_manual.py # Manual script for testing streaming chat functionality.
│   │   └── test_well_known.py # Contract test for the JWKS endpoint.
│   ├── fixtures/              # Test fixture data files.
│   │   ├── keysets/           # Test JSON Web Key Sets.
│   │   └── stripe/            # Sample Stripe webhook event payloads.
│   ├── integration/           # Tests requiring external services like a database.
│   │   ├── __init__.py        # Initializes the integration tests package.
│   │   ├── test_billing_stream.py # Integration tests for the server-sent events billing stream.
│   │   ├── test_postgres_migrations.py # Integration tests for Alembic migrations and database repositories.
│   │   ├── test_stripe_replay_cli.py # Integration tests for the Stripe event replay CLI script.
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook endpoint.
│   ├── unit/                  # Unit tests for individual modules with mocked dependencies.
│   │   ├── test_auth_domain.py # Unit tests for authentication domain logic helpers.
│   │   ├── test_auth_service.py # Unit tests for the main authentication service facade.
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic.
│   │   ├── test_billing_events.py # Unit tests for the billing event broadcasting service.
│   │   ├── test_billing_service.py # Unit tests for the billing service logic.
│   │   ├── test_config.py     # Unit tests for application settings validation and helpers.
│   │   ├── test_email_templates.py # Unit tests for email template rendering.
│   │   ├── test_email_verification_service.py # Unit tests for the email verification service.
│   │   ├── test_keys.py       # Unit tests for cryptographic key management logic.
│   │   ├── test_keys_cli.py   # Unit tests for the key management CLI commands.
│   │   ├── test_metrics.py    # Unit tests for Prometheus metrics helpers.
│   │   ├── test_nonce_store.py # Unit tests for the nonce replay-protection store.
│   │   ├── test_password_recovery_service.py # Unit tests for the password recovery service.
│   │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
│   │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository logic.
│   │   ├── test_resend_adapter.py # Unit tests for the Resend email notification adapter.
│   │   ├── test_scope_dependencies.py # Unit tests for FastAPI scope dependency logic.
│   │   ├── test_secret_guard.py # Unit tests for production secret enforcement logic.
│   │   ├── test_security.py   # Unit tests for core security functions (JWT, passwords).
│   │   ├── test_signup_service.py # Unit tests for the user/tenant signup orchestration service.
│   │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher logic.
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│   │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry worker.
│   │   ├── test_tenant_dependency.py # Unit tests for the multi-tenancy dependency logic.
│   │   ├── test_tools.py      # Unit tests for the agent tool registry and tools.
│   │   ├── test_user_models.py # Unit tests for user-related SQLAlchemy ORM models.
│   │   ├── test_user_repository.py # Unit tests for the user data repository.
│   │   ├── test_user_service.py # Unit tests for the user domain service.
│   │   ├── test_vault_client.py # Unit tests for the Vault Transit client.
│   │   └── test_vault_kv.py   # Unit tests for the Vault KV client.
│   └── utils/                 # Utility helpers for tests.
│       ├── fake_billing_backend.py # A fake billing event backend for testing.
│       └── sqlalchemy.py      # SQLAlchemy test helpers.
└── var/                       # Directory for variable data generated at runtime.
    └── keys/                  # Default directory for storing cryptographic keys on disk.
```