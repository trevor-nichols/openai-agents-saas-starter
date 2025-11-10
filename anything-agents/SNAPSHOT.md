.
├── alembic/                    # Contains Alembic database migration configuration and scripts.
│   ├── env.py                 # Alembic's main configuration script for running migrations.
│   └── script.py.mako         # Template for generating new Alembic migration scripts.
├── alembic.ini                  # Configuration file for the Alembic database migration tool.
├── app/                         # Main application source code directory.
│   ├── __init__.py            # Marks the 'app' directory as a Python package.
│   ├── api/                     # Defines the FastAPI API layer, including routers, models, and dependencies.
│   │   ├── __init__.py        # Marks the 'api' directory as a Python package.
│   │   ├── dependencies/        # Contains FastAPI dependency injection helpers.
│   │   │   ├── __init__.py    # Exposes shared dependency helpers for easier importing.
│   │   │   ├── auth.py        # FastAPI dependencies for authentication and scope-based authorization.
│   │   │   ├── common.py      # Common API dependencies, such as pagination parameters.
│   │   │   ├── rate_limit.py  # Dependency helper for handling rate limit errors.
│   │   │   └── tenant.py      # FastAPI dependencies for multi-tenancy context and role enforcement.
│   │   ├── errors.py          # Centralized exception handler registration for the FastAPI app.
│   │   ├── models/            # Pydantic models for API request and response bodies.
│   │   │   ├── __init__.py    # Marks the 'models' directory as a Python package.
│   │   │   ├── auth.py        # Pydantic models for authentication-related API requests and responses.
│   │   │   └── common.py      # Common Pydantic models for API responses (success, error, pagination).
│   │   ├── router.py          # Top-level API router that aggregates versioned routers.
│   │   └── v1/                  # Contains the version 1 API endpoints.
│   │       ├── __init__.py    # Marks the 'v1' directory as a Python package.
│   │       ├── agents/        # API endpoints for managing and interacting with agents.
│   │       │   ├── __init__.py # Marks the 'agents' API directory as a Python package.
│   │       │   ├── router.py    # FastAPI router for agent catalog and status endpoints.
│   │       │   └── schemas.py   # Pydantic schemas for the agent API endpoints.
│   │       ├── auth/          # API endpoints for authentication and user management.
│   │       │   ├── __init__.py # Marks the 'auth' API directory as a Python package.
│   │       │   ├── router.py    # Aggregates all authentication-related API routes.
│   │       │   ├── routes_email.py # API routes for email verification workflows.
│   │       │   ├── routes_passwords.py # API routes for password management (forgot, reset, change).
│   │       │   ├── routes_service_accounts.py # API route for issuing service account tokens.
│   │       │   ├── routes_sessions.py # API routes for user session management (login, logout, refresh).
│   │       │   ├── routes_signup.py # API route for public user and tenant registration.
│   │       │   └── utils.py     # Utility functions for the authentication API routes.
│   │       ├── billing/       # API endpoints for billing and subscription management.
│   │       │   ├── __init__.py # Marks the 'billing' API directory as a Python package.
│   │       │   ├── router.py    # FastAPI router for billing plans, subscriptions, and usage.
│   │       │   └── schemas.py   # Pydantic schemas for the billing API endpoints.
│   │       ├── chat/          # API endpoints for chat interactions with agents.
│   │       │   ├── __init__.py # Marks the 'chat' API directory as a Python package.
│   │       │   ├── router.py    # FastAPI router for handling chat and streaming chat requests.
│   │       │   └── schemas.py   # Pydantic schemas for chat API requests and responses.
│   │       ├── conversations/ # API endpoints for managing conversation history.
│   │       │   ├── __init__.py # Marks the 'conversations' API directory as a Python package.
│   │       │   ├── router.py    # FastAPI router for listing and managing conversation history.
│   │       │   └── schemas.py   # Pydantic schemas for conversation history API endpoints.
│   │       ├── router.py        # Aggregates all v1 API endpoint routers.
│   │       └── tools/         # API endpoints for inspecting available agent tools.
│   │           ├── __init__.py # Marks the 'tools' API directory as a Python package.
│   │           └── router.py    # FastAPI router for listing available agent tools.
│   ├── cli/                     # Contains command-line interface logic.
│   │   └── __init__.py          # Marks the 'cli' directory as a Python package for command-line utilities.
│   ├── core/                    # Core application logic, configuration, and security components.
│   │   ├── __init__.py          # Marks the 'core' directory as a Python package.
│   │   ├── config.py            # Defines application settings using Pydantic's BaseSettings.
│   │   ├── keys.py              # Re-exports shared key management utilities.
│   │   ├── password_policy.py   # Defines and validates password strength requirements.
│   │   ├── security.py          # Handles JWTs, password hashing, and auth dependencies.
│   │   ├── service_accounts.py  # Defines and loads the service account catalog.
│   │   └── service_accounts.yaml # YAML configuration defining available service accounts and their permissions.
│   ├── domain/                  # Defines core business logic, models (DTOs), and repository interfaces.
│   │   ├── __init__.py          # Marks the 'domain' directory as a Python package.
│   │   ├── auth.py              # Defines domain models and repository interfaces for authentication.
│   │   ├── billing.py           # Defines domain models and repository interfaces for billing.
│   │   ├── conversations.py     # Defines domain models and repository interfaces for conversations.
│   │   ├── email_verification.py # Defines domain models and store interface for email verification.
│   │   ├── password_reset.py    # Defines domain models and store interface for password reset tokens.
│   │   └── users.py             # Defines domain models and repository interfaces for users.
│   ├── infrastructure/          # Implementation of external-facing components (database, APIs, etc.).
│   │   ├── __init__.py          # Marks the 'infrastructure' directory as a Python package.
│   │   ├── db/                  # Database connection and session management.
│   │   │   ├── __init__.py      # Exposes database engine and session helpers.
│   │   │   ├── engine.py        # Manages the global SQLAlchemy async engine and session factory.
│   │   │   └── session.py       # FastAPI dependency for providing database sessions to routes.
│   │   ├── notifications/       # Adapters for sending notifications, like emails via Resend.
│   │   │   ├── __init__.py      # Exposes notification adapters.
│   │   │   └── resend.py        # Adapter for sending transactional emails via the Resend API.
│   │   ├── openai/              # Wrappers and session management for the OpenAI Agents SDK.
│   │   │   ├── __init__.py      # Marks the 'openai' infrastructure directory as a Python package.
│   │   │   ├── runner.py        # Wrapper around the OpenAI Agents SDK runner for executing agents.
│   │   │   └── sessions.py      # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/         # Implementation of the data persistence layer (repositories).
│   │   │   ├── __init__.py      # Marks the 'persistence' directory as a Python package.
│   │   │   ├── auth/            # Repositories for authentication-related data (users, sessions).
│   │   │   │   ├── cache.py     # Redis-based cache for refresh tokens.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for users, tenants, sessions, and tokens.
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository.
│   │   │   │   ├── session_repository.py # Postgres implementation of the user session repository.
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository with Redis for lockouts.
│   │   │   ├── billing/       # Repository for billing data.
│   │   │   │   ├── __init__.py  # Exposes billing repository implementations.
│   │   │   │   └── postgres.py  # Postgres implementation of the billing repository.
│   │   │   ├── conversations/ # Repositories for conversation data.
│   │   │   │   ├── __init__.py  # Exposes conversation repository implementations.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for conversations, tenants, and billing entities.
│   │   │   │   └── postgres.py  # Postgres implementation of the conversation repository.
│   │   │   ├── models/        # Shared base for SQLAlchemy models.
│   │   │   │   └── base.py      # Defines the base SQLAlchemy model with shared metadata.
│   │   │   ├── stripe/        # Repository for Stripe event data.
│   │   │   │   ├── models.py    # SQLAlchemy ORM models for storing Stripe events and dispatches.
│   │   │   │   └── repository.py # Postgres implementation of the Stripe event repository.
│   │   │   └── tenants/       # (Empty) Placeholder for tenant-specific persistence.
│   │   ├── security/            # Security-related infrastructure components like token stores and Vault clients.
│   │   │   ├── email_verification_store.py # Redis implementation of the email verification token store.
│   │   │   ├── nonce_store.py   # Redis-backed store for preventing replay attacks.
│   │   │   ├── password_reset_store.py # Redis implementation of the password reset token store.
│   │   │   ├── vault.py         # Client for interacting with HashiCorp Vault's Transit secret engine.
│   │   │   └── vault_kv.py      # Re-exports shared Vault KV utilities.
│   │   └── stripe/              # A typed client for interacting with the Stripe API.
│   │       ├── __init__.py      # Exposes the typed Stripe client.
│   │       ├── client.py        # A typed, retry-aware client wrapper for the Stripe API.
│   │       └── types.py         # Type definitions and shims for the dynamic Stripe Python SDK.
│   ├── middleware/              # Custom FastAPI middleware.
│   │   ├── __init__.py          # Marks the 'middleware' directory as a Python package.
│   │   └── logging.py           # FastAPI middleware for logging requests and responses.
│   ├── observability/           # Logging and metrics components.
│   │   ├── __init__.py          # Marks the 'observability' directory as a Python package.
│   │   ├── logging.py           # Helper for structured JSON event logging.
│   │   └── metrics.py           # Defines and exposes Prometheus metrics for the application.
│   ├── presentation/            # Defines non-API HTTP endpoints like health checks and webhooks.
│   │   ├── __init__.py          # Marks the 'presentation' directory as a Python package.
│   │   ├── emails/              # Email template rendering logic.
│   │   │   ├── __init__.py      # Exposes email rendering functions.
│   │   │   └── templates.py     # Renders HTML and text for transactional emails.
│   │   ├── health.py            # Defines the `/health` and `/health/ready` endpoints.
│   │   ├── metrics.py           # Defines the `/metrics` endpoint for Prometheus scraping.
│   │   ├── webhooks/            # Webhook handlers for third-party services like Stripe.
│   │   │   ├── __init__.py      # Marks the 'webhooks' directory as a Python package.
│   │   │   └── stripe.py        # Defines the webhook endpoint for receiving Stripe events.
│   │   └── well_known.py        # Defines the `/.well-known/jwks.json` endpoint for public keys.
│   ├── services/                # Business logic services that orchestrate domain and infrastructure.
│   │   ├── __init__.py          # Marks the 'services' directory as a Python package.
│   │   ├── agent_service.py     # Core service for orchestrating agent interactions and managing tools.
│   │   ├── auth/                # Sub-services for handling different aspects of authentication.
│   │   │   ├── __init__.py      # Exposes authentication sub-services and errors.
│   │   │   ├── errors.py        # Custom exception classes for authentication services.
│   │   │   ├── refresh_token_manager.py # Service for managing the lifecycle of refresh tokens.
│   │   │   ├── service_account_service.py # Service for issuing and managing service account tokens.
│   │   │   ├── session_service.py # Service for managing human user sessions (login, refresh, etc.).
│   │   │   └── session_store.py # Service for persisting and enriching user session metadata.
│   │   ├── auth_service.py      # Façade that combines various authentication-related services.
│   │   ├── billing_events.py    # Service for broadcasting billing events to real-time subscribers.
│   │   ├── billing_service.py   # Service for managing billing plans and subscriptions.
│   │   ├── conversation_service.py # Service for managing and searching conversation histories.
│   │   ├── email_verification_service.py # Service for handling the email verification workflow.
│   │   ├── geoip_service.py     # A pluggable service for IP-based geolocation lookups.
│   │   ├── password_recovery_service.py # Service for handling the password recovery workflow.
│   │   ├── payment_gateway.py   # Defines the payment gateway interface and Stripe implementation.
│   │   ├── rate_limit_service.py # Redis-backed service for API rate limiting.
│   │   ├── signup_service.py    # Service for orchestrating new user and tenant signups.
│   │   ├── stripe_dispatcher.py # Service for dispatching Stripe webhook events to appropriate handlers.
│   │   ├── stripe_event_models.py # Shared data classes for Stripe event processing.
│   │   └── stripe_retry_worker.py # Background worker for retrying failed Stripe event dispatches.
│   └── utils/                   # General utility functions and helpers.
│       ├── __init__.py          # Marks the 'utils' directory as a Python package.
│       ├── tools/               # Utilities for managing and registering agent tools.
│       │   ├── __init__.py      # Exposes the tool registry and core tools.
│       │   ├── registry.py      # A central registry for managing tools available to agents.
│       │   └── web_search.py    # Implements a web search tool using the Tavily API.
│       └── user_agent.py        # A lightweight parser for extracting info from User-Agent strings.
├── main.py                      # Main entry point for the FastAPI application.
└── tests/                       # Contains all tests for the application.
    ├── __init__.py              # Marks the 'tests' directory as a Python package.
    ├── conftest.py              # Shared pytest fixtures for test setup and teardown.
    ├── contract/                # API contract tests using FastAPI's TestClient.
    │   ├── __init__.py          # Marks the 'contract' test directory as a package and sets test environment.
    │   ├── test_agents_api.py   # API contract tests for agent, chat, and conversation endpoints.
    │   ├── test_auth_service_accounts.py # API contract tests for service account token issuance.
    │   ├── test_auth_users.py   # API contract tests for human user authentication workflows.
    │   ├── test_health_endpoints.py # API contract tests for health and readiness endpoints.
    │   ├── test_metrics_endpoint.py # API contract test for the Prometheus /metrics endpoint.
    │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming behavior.
    │   └── test_well_known.py   # API contract test for the /.well-known/jwks.json endpoint.
    ├── fixtures/                # Test data fixtures.
    │   ├── keysets/             # Fixtures for cryptographic keysets.
    │   └── stripe/              # Fixtures for Stripe webhook events.
    ├── integration/             # Tests that require external services like a real database.
    │   ├── __init__.py          # Marks the 'integration' test directory as a Python package.
    │   ├── test_billing_stream.py # Integration tests for the server-sent events (SSE) billing stream.
    │   ├── test_postgres_migrations.py # Integration tests to verify database migrations and repository functionality.
    │   ├── test_stripe_replay_cli.py # Integration tests for the CLI tool that replays Stripe events.
    │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook endpoint.
    ├── unit/                    # Fast, isolated unit tests.
    │   ├── test_auth_domain.py  # Unit tests for authentication domain logic helpers.
    │   ├── test_auth_service.py # Unit tests for the authentication service layer.
    │   ├── test_auth_vault_claims.py # Unit tests for Vault claim validation logic.
    │   ├── test_billing_events.py # Unit tests for the billing events broadcasting service.
    │   ├── test_billing_service.py # Unit tests for the billing service layer.
    │   ├── test_cli_forbidden_imports.py # Linter-style test to prevent backend code imports in the CLI.
    │   ├── test_cli_imports.py  # Test to ensure CLI modules don't load settings on import.
    │   ├── test_cli_main.py     # Test to ensure the main CLI entrypoint works correctly.
    │   ├── test_config.py       # Unit tests for the application configuration loading and validation.
    │   ├── test_email_templates.py # Unit tests for email template rendering.
    │   ├── test_email_verification_service.py # Unit tests for the email verification service.
    │   ├── test_keys.py         # Unit tests for cryptographic key management.
    │   ├── test_keys_cli.py     # Unit tests for the key management CLI commands.
    │   ├── test_metrics.py      # Unit tests for Prometheus metrics helpers.
    │   ├── test_nonce_store.py  # Unit tests for the nonce store used for replay protection.
    │   ├── test_password_recovery_service.py # Unit tests for the password recovery service.
    │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
    │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository logic.
    │   ├── test_resend_adapter.py # Unit tests for the Resend email API adapter.
    │   ├── test_scope_dependencies.py # Unit tests for API scope dependency helpers.
    │   ├── test_secret_guard.py # Unit tests for production secret validation logic.
    │   ├── test_security.py     # Unit tests for core security functions like JWT signing/verifying.
    │   ├── test_setup_inputs.py # Unit tests for the setup wizard's input providers.
    │   ├── test_setup_validators.py # Unit tests for the setup wizard's validation functions.
    │   ├── test_setup_wizard.py # Unit tests for the setup wizard orchestration.
    │   ├── test_signup_service.py # Unit tests for the user signup orchestration service.
    │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher logic.
    │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
    │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
    │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe event retry worker.
    │   ├── test_tenant_dependency.py # Unit tests for the multi-tenancy dependency logic.
    │   ├── test_tools.py        # Unit tests for the agent tool registry and individual tools.
    │   ├── test_user_models.py  # Unit tests for SQLAlchemy user model definitions.
    │   ├── test_user_repository.py # Unit tests for the user repository implementation.
    │   ├── test_user_service.py # Unit tests for the user service logic.
    │   ├── test_vault_client.py # Unit tests for the Vault Transit client.
    │   └── test_vault_kv.py     # Unit tests for the Vault KV secrets client.
    └── utils/                   # Utility functions for tests.
        ├── fake_billing_backend.py # A fake billing event backend for use in tests.
        └── sqlalchemy.py        # SQLAlchemy test helpers, like for table creation.