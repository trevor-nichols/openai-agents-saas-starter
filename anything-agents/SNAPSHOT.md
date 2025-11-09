.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                 # Alembic environment setup for running database migrations asynchronously.
│   └── script.py.mako         # Mako template for generating new Alembic migration scripts.
├── alembic.ini                 # Configuration file for the Alembic database migration tool.
├── app/                        # Main application source code directory.
│   ├── __init__.py            # Initializes the 'app' package.
│   ├── api/                    # Contains the FastAPI API layer, including routers, dependencies, and models.
│   │   ├── __init__.py        # Initializes the 'api' package.
│   │   ├── dependencies/        # FastAPI dependencies for shared logic like auth, rate limiting, and tenancy.
│   │   │   ├── __init__.py    # Exposes shared FastAPI dependency injectors.
│   │   │   ├── auth.py        # FastAPI dependencies for authentication and scope validation.
│   │   │   ├── common.py      # Common FastAPI dependencies, like pagination parameters.
│   │   │   ├── rate_limit.py  # Helper for converting rate limit errors to HTTP 429 responses.
│   │   │   └── tenant.py      # FastAPI dependencies for handling multi-tenancy context.
│   │   ├── errors.py          # Centralized exception handlers for the API layer.
│   │   ├── models/            # Pydantic models for API request/response validation.
│   │   │   ├── __init__.py    # Initializes the API models package.
│   │   │   ├── auth.py        # Pydantic models for authentication-related API requests and responses.
│   │   │   └── common.py      # Common Pydantic models for API responses (e.g., Success, Error, Pagination).
│   │   ├── router.py          # Top-level API router, aggregates versioned routers (e.g., /v1).
│   │   └── v1/                # Contains the v1 version of the API.
│   │       ├── __init__.py    # Initializes the 'v1' API package.
│   │       ├── agents/        # API endpoints for managing and interacting with agents.
│   │       │   ├── __init__.py # Initializes the 'agents' API package.
│   │       │   ├── router.py  # API endpoints for listing available agents and checking their status.
│   │       │   └── schemas.py # Pydantic schemas for agent-related API responses.
│   │       ├── auth/          # API endpoints for authentication and authorization.
│   │       │   ├── __init__.py # Initializes the 'auth' API package.
│   │       │   ├── router.py  # Aggregates all authentication-related API endpoint routers.
│   │       │   ├── routes_email.py # API endpoints for handling email verification.
│   │       │   ├── routes_passwords.py # API endpoints for password management (change, reset, forgot).
│   │       │   ├── routes_service_accounts.py # API endpoint for issuing service account tokens with Vault integration.
│   │       │   ├── routes_sessions.py # API endpoints for user session management (login, logout, refresh).
│   │       │   ├── routes_signup.py # API endpoint for public user and tenant registration.
│   │       │   └── utils.py   # Utility functions for the authentication API endpoints.
│   │       ├── billing/       # API endpoints for billing and subscription management.
│   │       │   ├── __init__.py # Initializes the 'billing' API package.
│   │       │   ├── router.py  # API endpoints for managing billing, subscriptions, and usage.
│   │       │   └── schemas.py # Pydantic schemas for billing-related API requests and responses.
│   │       ├── chat/          # API endpoints for chat interactions, including streaming.
│   │       │   ├── __init__.py # Initializes the 'chat' API package.
│   │       │   ├── router.py  # API endpoints for synchronous and streaming chat with agents.
│   │       │   └── schemas.py # Pydantic schemas for chat request and response models.
│   │       ├── conversations/ # API endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the 'conversations' API package.
│   │       │   ├── router.py  # API endpoints for listing, retrieving, and deleting conversation histories.
│   │       │   └── schemas.py # Pydantic schemas for conversation and message models.
│   │       ├── router.py      # Aggregates all routers for the v1 API.
│   │       └── tools/         # API endpoints for listing available agent tools.
│   │           ├── __init__.py # Initializes the 'tools' API package.
│   │           └── router.py  # API endpoint for listing available agent tools.
│   ├── cli/                    # Command-line interface scripts for the application.
│   │   ├── __init__.py        # Initializes the command-line interface package.
│   │   └── auth_cli.py        # Command-line interface for auth tasks like issuing service account tokens.
│   ├── core/                   # Core application logic, configuration, and security components.
│   │   ├── __init__.py        # Initializes the 'core' application logic package.
│   │   ├── config.py          # Pydantic-based settings management, loading from environment variables.
│   │   ├── keys.py            # Manages cryptographic keys (Ed25519) for JWT signing.
│   │   ├── password_policy.py # Centralized password strength validation logic.
│   │   ├── security.py        # JWT and password hashing utilities, plus token signer/verifier abstractions.
│   │   ├── service_accounts.py # Loads and manages service account definitions from a YAML catalog.
│   │   └── service_accounts.yaml # YAML catalog defining available service accounts and their permissions.
│   ├── domain/                 # Defines the core business logic, entities, and repository interfaces (contracts).
│   │   ├── __init__.py        # Initializes the domain logic package.
│   │   ├── auth.py            # Domain models and repository contracts for authentication.
│   │   ├── billing.py         # Domain models and repository contracts for billing.
│   │   ├── conversations.py   # Domain models and repository contracts for conversations.
│   │   ├── email_verification.py # Domain models and repository contracts for email verification tokens.
│   │   ├── password_reset.py  # Domain models and repository contracts for password reset tokens.
│   │   └── users.py           # Domain models and repository contracts for user management.
│   ├── infrastructure/         # Implementation of the domain repository interfaces, interacting with external systems (DB, caches, APIs).
│   │   ├── __init__.py        # Initializes the infrastructure implementation package.
│   │   ├── db/                # Database connection and session management (SQLAlchemy).
│   │   │   ├── __init__.py    # Exposes core database engine and session management functions.
│   │   │   ├── engine.py      # Manages the lifecycle of the asynchronous SQLAlchemy engine.
│   │   │   └── session.py     # FastAPI dependency for providing database sessions to endpoints.
│   │   ├── openai/            # Wrappers and session management for the OpenAI Agents SDK.
│   │   │   ├── __init__.py    # Initializes the OpenAI SDK integration package.
│   │   │   ├── runner.py      # Wrapper around the OpenAI Agents SDK runner for executing agents.
│   │   │   └── sessions.py    # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/       # Data persistence implementations (repositories).
│   │   │   ├── __init__.py    # Initializes the data persistence package.
│   │   │   ├── auth/          # Persistence logic for authentication-related data.
│   │   │   │   ├── cache.py   # Redis-backed cache for refresh token lookups.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for users, tenants, and auth tokens.
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository.
│   │   │   │   ├── session_repository.py # Postgres implementation of the user session repository.
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository with Redis for lockouts.
│   │   │   ├── billing/       # Persistence logic for billing data.
│   │   │   │   ├── __init__.py # Initializes the billing persistence package.
│   │   │   │   └── postgres.py # Postgres implementation of the billing repository.
│   │   │   ├── conversations/ # Persistence logic for conversation data.
│   │   │   │   ├── __init__.py # Initializes the conversations persistence package.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for conversations, tenants, and billing entities.
│   │   │   │   └── postgres.py # Postgres implementation of the conversation repository.
│   │   │   ├── models/        # Shared base for SQLAlchemy ORM models.
│   │   │   │   └── base.py    # Defines the base SQLAlchemy model with shared metadata.
│   │   │   ├── stripe/        # Persistence logic for Stripe webhook events.
│   │   │   │   ├── models.py  # SQLAlchemy ORM models for storing Stripe webhook events.
│   │   │   │   └── repository.py # Postgres implementation for storing and managing Stripe events.
│   │   │   └── tenants/       # (Empty directory) Potentially for tenant-specific persistence.
│   │   ├── security/          # Security-related infrastructure components (e.g., Vault, token stores).
│   │   │   ├── email_verification_store.py # Redis implementation of the email verification token store.
│   │   │   ├── nonce_store.py # Redis-backed store for nonce replay protection.
│   │   │   ├── password_reset_store.py # Redis implementation of the password reset token store.
│   │   │   ├── vault.py       # Client for interacting with HashiCorp Vault's Transit engine.
│   │   │   └── vault_kv.py    # Client for interacting with HashiCorp Vault's KV secret engine.
│   │   └── stripe/            # Client wrappers for interacting with the Stripe API.
│   │       ├── __init__.py    # Initializes the Stripe client package.
│   │       ├── client.py      # Typed client wrapper for the Stripe API with retries.
│   │       └── types.py       # Type definitions and wrappers for the dynamic Stripe SDK.
│   ├── middleware/             # Custom FastAPI middleware.
│   │   ├── __init__.py        # Initializes the middleware package.
│   │   └── logging.py         # FastAPI middleware for request and response logging.
│   ├── observability/          # Logging and metrics setup.
│   │   ├── __init__.py        # Initializes the observability package.
│   │   ├── logging.py         # Helper for structured, event-based logging.
│   │   └── metrics.py         # Defines and manages Prometheus metrics for the application.
│   ├── presentation/           # Non-API presentation layer (e.g., health checks, webhooks).
│   │   ├── __init__.py        # Initializes the presentation layer package.
│   │   ├── health.py          # Health and readiness check API endpoints.
│   │   ├── metrics.py         # API endpoint for exposing Prometheus metrics.
│   │   ├── webhooks/          # Webhook handlers for external services like Stripe.
│   │   │   ├── __init__.py    # Initializes the webhooks package.
│   │   │   └── stripe.py      # API endpoint for receiving and processing Stripe webhooks.
│   │   └── well_known.py      # API endpoint for serving /.well-known/jwks.json.
│   ├── services/               # Business service layer, orchestrating domain logic and infrastructure.
│   │   ├── __init__.py        # Initializes the service layer package.
│   │   ├── agent_service.py   # Core service for orchestrating agent interactions and managing tools.
│   │   ├── auth/              # Sub-package for specialized authentication services.
│   │   │   ├── __init__.py    # Initializes the auth sub-services package.
│   │   │   ├── errors.py      # Custom exception classes for authentication services.
│   │   │   ├── refresh_token_manager.py # Manages the lifecycle of refresh tokens.
│   │   │   ├── service_account_service.py # Service for issuing and managing service account tokens.
│   │   │   ├── session_service.py # Service for managing human user sessions (login, refresh, logout).
│   │   │   └── session_store.py # High-level service for persisting user session metadata.
│   │   ├── auth_service.py    # Facade that orchestrates various authentication sub-services.
│   │   ├── billing_events.py  # Service for broadcasting billing events via a stream (e.g., Redis).
│   │   ├── billing_service.py # Service for managing billing plans and subscriptions.
│   │   ├── conversation_service.py # Service for managing conversation history and state.
│   │   ├── email_verification_service.py # Service for handling email verification flows.
│   │   ├── geoip_service.py   # Pluggable service for GeoIP lookups (stub implementation).
│   │   ├── password_recovery_service.py # Service for handling password reset and recovery flows.
│   │   ├── payment_gateway.py # Abstraction layer for payment providers, with a Stripe implementation.
│   │   ├── rate_limit_service.py # Redis-backed service for API rate limiting.
│   │   ├── signup_service.py  # Service orchestrating user and tenant self-service registration.
│   │   ├── stripe_dispatcher.py # Service for routing Stripe webhook events to appropriate handlers.
│   │   ├── stripe_event_models.py # Dataclasses for Stripe webhook dispatch and event streams.
│   │   ├── stripe_retry_worker.py # Background worker for retrying failed Stripe event dispatches.
│   │   └── user_service.py    # Service for user management, authentication logic, and lockouts.
│   └── utils/                  # General utility functions and helpers.
│       ├── __init__.py        # Initializes the utility package.
│       ├── tools/             # Utility for managing and registering agent tools.
│       │   ├── __init__.py    # Exposes the tool registry and initialization functions.
│       │   ├── registry.py    # Central registry for managing and organizing tools available to agents.
│       │   └── web_search.py  # Implements a web search tool using the Tavily API.
│       └── user_agent.py      # Lightweight parser for extracting browser/platform from user-agent strings.
├── main.py                     # Main FastAPI application entry point, configuration, and lifespan management.
├── tests/                      # Contains all tests for the application.
│   ├── __init__.py            # Initializes the test suite package.
│   ├── conftest.py            # Shared pytest fixtures and configuration for the test suite.
│   ├── contract/              # API contract tests using the FastAPI TestClient.
│   │   ├── test_agents_api.py # API contract tests for agent, chat, and conversation endpoints.
│   │   ├── test_auth_service_accounts.py # API contract tests for service account token issuance via CLI.
│   │   ├── test_auth_users.py # API contract tests for human user authentication endpoints.
│   │   ├── test_health_endpoints.py # API contract tests for health and readiness endpoints.
│   │   ├── test_metrics_endpoint.py # API contract test for the Prometheus metrics endpoint.
│   │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming chat functionality.
│   │   └── test_well_known.py # API contract test for the JWKS endpoint.
│   ├── fixtures/              # Test data and fixtures.
│   │   ├── keysets/           # Directory for test cryptographic keysets.
│   │   └── stripe/            # Directory for Stripe webhook event fixture files.
│   ├── integration/           # Tests that require external services like a database.
│   │   ├── __init__.py        # Initializes the integration test package.
│   │   ├── test_billing_stream.py # Integration tests for the server-sent events (SSE) billing stream.
│   │   ├── test_postgres_migrations.py # Integration tests verifying database migrations and repository functionality.
│   │   ├── test_stripe_replay_cli.py # Integration tests for the Stripe event replay CLI script.
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook ingestion endpoint.
│   ├── unit/                  # Unit tests for individual components with mocks.
│   │   ├── test_auth_domain.py # Unit tests for authentication domain logic helpers.
│   │   ├── test_auth_service.py # Unit tests for the main authentication service facade.
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic.
│   │   ├── test_billing_events.py # Unit tests for the billing events broadcasting service.
│   │   ├── test_billing_service.py # Unit tests for the billing service logic.
│   │   ├── test_config.py     # Unit tests for application settings and configuration parsing.
│   │   ├── test_email_verification_service.py # Unit tests for the email verification service.
│   │   ├── test_keys.py       # Unit tests for cryptographic key management utilities.
│   │   ├── test_keys_cli.py   # Unit tests for the key management command-line interface.
│   │   ├── test_metrics.py    # Unit tests for Prometheus metrics helpers.
│   │   ├── test_nonce_store.py # Unit tests for the nonce replay-protection store.
│   │   ├── test_password_recovery_service.py # Unit tests for the password recovery service.
│   │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
│   │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository logic.
│   │   ├── test_scope_dependencies.py # Unit tests for JWT scope parsing and enforcement dependencies.
│   │   ├── test_secret_guard.py # Unit tests for production secret enforcement logic.
│   │   ├── test_security.py   # Unit tests for security utilities like JWT signing/verifying.
│   │   ├── test_signup_service.py # Unit tests for the user/tenant signup service.
│   │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher logic.
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event persistence repository.
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│   │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry background worker.
│   │   ├── test_tenant_dependency.py # Unit tests for the multi-tenancy context dependency.
│   │   ├── test_tools.py      # Unit tests for the agent tool registry and tools.
│   │   ├── test_user_models.py # Unit tests for user-related SQLAlchemy ORM models.
│   │   ├── test_user_repository.py # Unit tests for the user persistence repository.
│   │   ├── test_user_service.py # Unit tests for the user management domain service.
│   │   ├── test_vault_client.py # Unit tests for the HashiCorp Vault Transit client.
│   │   └── test_vault_kv.py   # Unit tests for the HashiCorp Vault KV client.
│   └── utils/                 # Utility helpers for tests.
│       ├── fake_billing_backend.py # A fake billing event backend for use in tests.
│       └── sqlalchemy.py      # SQLAlchemy helper functions for tests.
└── var/                        # Variable data, like stored keys.
    └── keys/                   # Default directory for storing cryptographic keys on the filesystem.