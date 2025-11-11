.
├── alembic/                   # Contains Alembic database migration scripts and configuration.
│   ├── env.py                # Alembic's main configuration script, defines how migrations run.
│   └── script.py.mako        # Template for generating new Alembic migration scripts.
├── alembic.ini                # Configuration file for the Alembic database migration tool.
├── app/                       # Main application source code directory.
│   ├── __init__.py           # Initializes the 'app' package.
│   ├── api/                   # Contains all API-related code (endpoints, schemas, dependencies).
│   │   ├── __init__.py       # Initializes the 'api' subpackage.
│   │   ├── dependencies/      # FastAPI dependencies for shared logic like auth, pagination, and tenancy.
│   │   │   ├── __init__.py   # Exposes shared dependency helpers for easy import.
│   │   │   ├── auth.py       # Dependencies for authentication, authorization, and scope enforcement.
│   │   │   ├── common.py     # Shared dependencies like pagination parameters.
│   │   │   ├── rate_limit.py # Helper to translate rate limit errors into HTTP 429 responses.
│   │   │   ├── service_accounts.py # Dependencies for service account administration and actor resolution.
│   │   │   └── tenant.py     # Dependencies for resolving and validating multi-tenant context.
│   │   ├── errors.py          # Centralized exception handling for the API.
│   │   ├── models/            # Pydantic models for API request/response bodies.
│   │   │   ├── __init__.py   # Initializes the 'models' subpackage.
│   │   │   ├── auth.py       # Pydantic models for authentication-related requests and responses.
│   │   │   └── common.py     # Common API models like SuccessResponse and ErrorResponse.
│   │   ├── router.py          # Top-level API router that aggregates versioned routers.
│   │   └── v1/                # Contains the V1 version of the API.
│   │       ├── __init__.py   # Initializes the 'v1' subpackage.
│   │       ├── agents/       # API endpoints for managing and listing agents.
│   │       │   ├── __init__.py # Initializes the 'agents' subpackage.
│   │       │   ├── router.py # FastAPI router for agent catalog endpoints.
│   │       │   └── schemas.py # Pydantic schemas for agent-related API models.
│   │       ├── auth/         # API endpoints for authentication and authorization.
│   │       │   ├── __init__.py # Initializes the 'auth' subpackage.
│   │       │   ├── router.py # Aggregates all authentication-related routers.
│   │       │   ├── routes_email.py # API routes for email verification.
│   │       │   ├── routes_passwords.py # API routes for password management (forgot, reset, change).
│   │       │   ├── routes_service_account_tokens.py # API routes for managing service account tokens (list, revoke).
│   │       │   ├── routes_service_accounts.py # API route for issuing service account tokens.
│   │       │   ├── routes_sessions.py # API routes for user session management (login, logout, refresh).
│   │       │   ├── routes_signup.py # API route for public user and tenant registration.
│   │       │   └── utils.py    # Utility functions for the auth API routes (e.g., IP extraction).
│   │       ├── billing/      # API endpoints for billing and subscription management.
│   │       │   ├── __init__.py # Initializes the 'billing' subpackage.
│   │       │   ├── router.py # FastAPI router for billing, subscription, and usage endpoints.
│   │       │   └── schemas.py # Pydantic schemas for billing-related API models.
│   │       ├── chat/         # API endpoints for interacting with chat agents.
│   │       │   ├── __init__.py # Initializes the 'chat' subpackage.
│   │       │   ├── router.py # FastAPI router for chat and streaming chat endpoints.
│   │       │   └── schemas.py # Pydantic schemas for chat request and response models.
│   │       ├── conversations/ # API endpoints for managing conversation history.
│   │       │   ├── __init__.py # Initializes the 'conversations' subpackage.
│   │       │   ├── router.py # FastAPI router for listing, getting, and deleting conversations.
│   │       │   └── schemas.py # Pydantic schemas for conversation history and messages.
│   │       ├── router.py     # Aggregates all routers for the V1 API.
│   │       └── tools/        # API endpoints for listing available agent tools.
│   │           ├── __init__.py # Initializes the 'tools' subpackage.
│   │           └── router.py # FastAPI router for listing available agent tools.
│   ├── bootstrap/             # Application startup and dependency injection setup.
│   │   ├── __init__.py       # Exposes the application container and its helpers.
│   │   └── container.py      # Defines the central dependency injection container for the application.
│   ├── cli/                   # Command-line interface utilities.
│   │   └── __init__.py       # Initializes the 'cli' package.
│   ├── core/                  # Core application logic, configuration, and security.
│   │   ├── __init__.py       # Initializes the 'core' package.
│   │   ├── config.py         # Pydantic-based application settings management.
│   │   ├── keys.py           # Re-exports shared key management helpers.
│   │   ├── password_policy.py # Centralized password strength validation logic.
│   │   ├── security.py       # JWT, password hashing, and token signing/verification utilities.
│   │   ├── service_accounts.py # Defines and loads the service account catalog.
│   │   └── service_accounts.yaml # YAML definition of available service accounts and their scopes.
│   ├── domain/                # Core business logic and domain models (DTOs, repository protocols).
│   │   ├── __init__.py       # Initializes the 'domain' package.
│   │   ├── auth.py           # Domain models and repository protocols for authentication.
│   │   ├── billing.py        # Domain models and repository protocols for billing.
│   │   ├── conversations.py  # Domain models and repository protocols for conversations.
│   │   ├── email_verification.py # Domain models and store protocol for email verification tokens.
│   │   ├── password_reset.py # Domain models and store protocol for password reset tokens.
│   │   └── users.py          # Domain models and repository protocols for user management.
│   ├── infrastructure/        # Adapters for external systems (database, caches, APIs).
│   │   ├── __init__.py       # Initializes the 'infrastructure' package.
│   │   ├── db/               # Database connection management (SQLAlchemy engine, sessions).
│   │   │   ├── __init__.py   # Exposes database engine and session helpers.
│   │   │   ├── engine.py     # Manages the SQLAlchemy async engine and migrations.
│   │   │   └── session.py    # FastAPI dependency for providing database sessions.
│   │   ├── notifications/     # Adapters for sending notifications like emails.
│   │   │   ├── __init__.py   # Exposes notification adapters.
│   │   │   └── resend.py     # Adapter for sending transactional emails via the Resend API.
│   │   ├── openai/            # Wrappers for the OpenAI Agents SDK.
│   │   │   ├── __init__.py   # Initializes the 'openai' subpackage.
│   │   │   ├── runner.py     # Wrapper around the OpenAI Agents SDK `Runner` for executing agents.
│   │   │   └── sessions.py   # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/       # Data persistence layer implementations (repositories).
│   │   │   ├── __init__.py   # Initializes the 'persistence' subpackage.
│   │   │   ├── auth/         # Persistence implementations for authentication-related data.
│   │   │   │   ├── cache.py    # Redis-backed cache for refresh tokens.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for users, tokens, and auth-related tables.
│   │   │   │   ├── repository.py # Postgres-backed repository for refresh tokens.
│   │   │   │   ├── session_repository.py # Postgres-backed repository for user session metadata.
│   │   │   │   └── user_repository.py # Postgres-backed repository for user accounts.
│   │   │   ├── billing/      # Persistence implementations for billing data.
│   │   │   │   ├── __init__.py # Exposes billing persistence adapters.
│   │   │   │   ├── models.py # SQLAlchemy ORM models for billing (plans, subscriptions, etc.).
│   │   │   │   └── postgres.py # Postgres-backed repository for billing data.
│   │   │   ├── conversations/ # Persistence implementations for conversation data.
│   │   │   │   ├── __init__.py # Exposes conversation persistence adapters.
│   │   │   │   ├── models.py # SQLAlchemy ORM models for tenants, conversations, and messages.
│   │   │   │   └── postgres.py # Postgres-backed repository for conversation history.
│   │   │   ├── models/       # Shared base models for persistence.
│   │   │   │   └── base.py   # Shared SQLAlchemy declarative base and helper functions.
│   │   │   ├── stripe/       # Persistence implementations for Stripe data.
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for Stripe events and dispatch records.
│   │   │   │   └── repository.py # Repository for storing and managing Stripe webhook events.
│   │   │   └── tenants/      # Directory for tenant persistence (currently empty).
│   │   ├── security/          # Adapters for security-related stores (e.g., tokens, secrets).
│   │   │   ├── email_verification_store.py # Redis-backed store for email verification tokens.
│   │   │   ├── nonce_store.py # Redis-backed store for nonce replay protection.
│   │   │   ├── password_reset_store.py # Redis-backed store for password reset tokens.
│   │   │   ├── vault.py      # Client for HashiCorp Vault's Transit secret engine.
│   │   │   └── vault_kv.py   # Re-exports shared Vault KV secret manager helpers.
│   │   └── stripe/            # Adapters for interacting with the Stripe API.
│   │       ├── __init__.py   # Exposes the Stripe client and its models.
│   │       ├── client.py     # Typed client for interacting with the Stripe API.
│   │       └── types.py      # Typing helpers and wrappers for the dynamic Stripe SDK.
│   ├── middleware/            # Custom FastAPI middleware.
│   │   ├── __init__.py       # Initializes the 'middleware' package.
│   │   └── logging.py        # Middleware for logging HTTP requests and responses.
│   ├── observability/         # Code for logging, metrics, and tracing.
│   │   ├── __init__.py       # Initializes the 'observability' package.
│   │   ├── logging.py        # Structured logging helper for application events.
│   │   └── metrics.py        # Defines and exposes Prometheus metrics.
│   ├── presentation/          # Code responsible for presenting data to external systems.
│   │   ├── __init__.py       # Initializes the 'presentation' package.
│   │   ├── emails/           # Utilities for rendering transactional email content.
│   │   │   ├── __init__.py   # Exposes email template rendering functions.
│   │   │   └── templates.py  # Renders HTML and text for transactional emails.
│   │   ├── health.py         # Health and readiness check endpoints.
│   │   ├── metrics.py        # Prometheus metrics scrape endpoint.
│   │   ├── webhooks/         # Endpoints for receiving webhooks from external services.
│   │   │   ├── __init__.py   # Initializes the 'webhooks' subpackage.
│   │   │   └── stripe.py     # Webhook endpoint for receiving Stripe events.
│   │   └── well_known.py     # Endpoints for /.well-known URIs, like JWKS.
│   ├── services/              # Business logic layer, orchestrating domain models and infrastructure.
│   │   ├── __init__.py       # Initializes the 'services' package.
│   │   ├── agent_service.py  # Core service for orchestrating agent interactions.
│   │   ├── auth/             # Sub-package for specialized authentication services.
│   │   │   ├── __init__.py   # Exposes specialized auth services and errors.
│   │   │   ├── builders.py   # Factory functions for constructing auth services.
│   │   │   ├── errors.py     # Custom error types for authentication services.
│   │   │   ├── refresh_token_manager.py # Manages the lifecycle of refresh tokens.
│   │   │   ├── service_account_service.py # Service for issuing and managing service account tokens.
│   │   │   ├── session_service.py # Service for managing human user sessions (login, refresh).
│   │   │   └── session_store.py # High-level service for persisting user session metadata.
│   │   ├── auth_service.py   # Facade that aggregates various authentication sub-services.
│   │   ├── billing_events.py # Service for broadcasting and streaming billing events.
│   │   ├── billing_service.py # Service for managing billing plans and subscriptions.
│   │   ├── conversation_service.py # Service for managing conversation history.
│   │   ├── email_verification_service.py # Service for handling email verification flows.
│   │   ├── geoip_service.py  # Pluggable service for IP-based geolocation lookups.
│   │   ├── password_recovery_service.py # Service for handling password reset flows.
│   │   ├── payment_gateway.py # Abstraction for payment providers like Stripe.
│   │   ├── rate_limit_service.py # Redis-backed service for rate limiting API requests.
│   │   ├── signup_service.py # Service for orchestrating new user/tenant signups.
│   │   ├── stripe_dispatcher.py # Service for routing Stripe webhook events to handlers.
│   │   ├── stripe_event_models.py # Shared data classes for Stripe webhook dispatching.
│   │   ├── stripe_retry_worker.py # Background worker for retrying failed Stripe event dispatches.
│   │   └── user_service.py   # Service for managing user accounts, authentication, and policies.
│   └── utils/                 # General utility functions and classes.
│       ├── __init__.py       # Initializes the 'utils' package.
│       ├── tools/            # Utilities for managing and registering agent tools.
│       │   ├── __init__.py   # Exposes the tool registry and its helpers.
│       │   ├── registry.py   # Central registry for managing agent tools.
│       │   └── web_search.py # Implements a web search tool using the Tavily API.
│       └── user_agent.py     # Lightweight parser for user-agent strings.
├── main.py                    # Main FastAPI application entry point and configuration.
└── tests/                     # Contains all tests for the application.
    ├── __init__.py           # Initializes the 'tests' package.
    ├── conftest.py            # Shared pytest fixtures and configuration for the test suite.
    ├── contract/              # Tests for the application's external contracts (APIs).
    │   ├── __init__.py       # Initializes the 'contract' test subpackage.
    │   ├── test_agents_api.py # Contract tests for the agent and chat API endpoints.
    │   ├── test_auth_service_account_tokens.py # Contract tests for service account token management endpoints.
    │   ├── test_auth_service_accounts.py # Contract tests for the service account token issuance endpoint.
    │   ├── test_auth_users.py # Contract tests for human user authentication endpoints.
    │   ├── test_health_endpoints.py # Contract tests for the /health and /health/ready endpoints.
    │   ├── test_metrics_endpoint.py # Contract tests for the /metrics endpoint.
    │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming behavior.
    │   └── test_well_known.py # Contract tests for the /.well-known/jwks.json endpoint.
    ├── fixtures/              # Test fixture data.
    │   ├── keysets/          # Keyset files for testing.
    │   └── stripe/           # Stripe webhook event fixture files.
    ├── integration/           # Tests that require external services like a real database.
    │   ├── __init__.py       # Initializes the 'integration' test subpackage.
    │   ├── test_billing_stream.py # Integration tests for the server-sent events billing stream.
    │   ├── test_postgres_migrations.py # Integration tests to verify database migrations and repositories.
    │   ├── test_stripe_replay_cli.py # Integration tests for the Stripe event replay CLI script.
    │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook endpoint.
    ├── unit/                  # Fast, isolated unit tests with mocked dependencies.
    │   ├── api/              # Unit tests for the API layer.
    │   │   └── test_routes_service_account_tokens.py # Unit tests for service account token route logic.
    │   ├── test_auth_domain.py # Unit tests for auth domain helpers like token hashing.
    │   ├── test_auth_service.py # Unit tests for the `AuthService` facade.
    │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic.
    │   ├── test_billing_events.py # Unit tests for the billing events service.
    │   ├── test_billing_service.py # Unit tests for the billing service logic.
    │   ├── test_cli_forbidden_imports.py # Linter-style test to prevent backend imports in the CLI.
    │   ├── test_cli_imports.py # Tests to ensure CLI modules import cleanly without side effects.
    │   ├── test_cli_main.py  # Unit tests for the main CLI entrypoint.
    │   ├── test_config.py    # Unit tests for the application settings class.
    │   ├── test_email_templates.py # Unit tests for email template rendering.
    │   ├── test_email_verification_service.py # Unit tests for the email verification service.
    │   ├── test_keys.py      # Unit tests for key generation and management.
    │   ├── test_keys_cli.py  # Unit tests for the key management CLI commands.
    │   ├── test_metrics.py   # Unit tests for Prometheus metric helpers.
    │   ├── test_nonce_store.py # Unit tests for the nonce store used in replay protection.
    │   ├── test_password_recovery_service.py # Unit tests for the password recovery service.
    │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
    │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository, especially rehydration.
    │   ├── test_resend_adapter.py # Unit tests for the Resend email API adapter.
    │   ├── test_scope_dependencies.py # Unit tests for API scope dependency helpers.
    │   ├── test_secret_guard.py # Unit tests for production secret enforcement logic.
    │   ├── test_security.py  # Unit tests for JWT signing, verification, and security dependencies.
    │   ├── test_service_account_token_service.py # Unit tests for the service account token issuance service.
    │   ├── test_setup_inputs.py # Unit tests for the CLI setup wizard's input providers.
    │   ├── test_setup_validators.py # Unit tests for the CLI setup wizard's input validators.
    │   ├── test_setup_wizard.py # Unit tests for the CLI setup wizard logic.
    │   ├── test_signup_service.py # Unit tests for the user/tenant signup service.
    │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher service.
    │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
    │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
    │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry worker.
    │   ├── test_tenant_dependency.py # Unit tests for the tenant context API dependency.
    │   ├── test_tools.py     # Unit tests for the agent tool registry and tools.
    │   ├── test_user_models.py # Unit tests for user-related SQLAlchemy ORM models.
    │   ├── test_user_repository.py # Unit tests for the user repository implementation.
    │   ├── test_user_service.py # Unit tests for the user management service.
    │   ├── test_vault_client.py # Unit tests for the Vault Transit client.
    │   └── test_vault_kv.py  # Unit tests for the Vault KV secret manager client.
    └── utils/                 # Utility functions for tests.
        ├── fake_billing_backend.py # A fake, in-memory billing event backend for testing.
        └── sqlalchemy.py     # Shared SQLAlchemy test helpers.