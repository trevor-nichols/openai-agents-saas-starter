.
├── alembic/                    # Contains Alembic database migration scripts and configuration.
│   ├── env.py                  # Alembic script that defines how migrations are run.
│   └── script.py.mako          # Mako template for generating new migration files.
├── alembic.ini                 # Configuration file for the Alembic database migration tool.
├── app/                        # Main application source code directory.
│   ├── __init__.py             # Initializes the 'app' package.
│   ├── api/                    # Contains all API-related code (FastAPI endpoints, schemas, dependencies).
│   │   ├── __init__.py           # Initializes the 'api' package.
│   │   ├── dependencies/         # FastAPI dependencies for common tasks like auth and pagination.
│   │   │   ├── __init__.py       # Exposes shared dependency helpers for easy import.
│   │   │   ├── auth.py           # Authentication and scope-based authorization dependencies.
│   │   │   ├── common.py         # Shared dependencies like pagination parameters.
│   │   │   ├── rate_limit.py     # Helper to translate rate limit errors into HTTP 429 responses.
│   │   │   ├── service_accounts.py # Dependencies for authenticating and authorizing service account actions.
│   │   │   └── tenant.py         # Dependencies for resolving tenant context and roles from requests.
│   │   ├── errors.py             # Centralized API exception handlers for FastAPI.
│   │   ├── models/               # Pydantic models (schemas) for API requests and responses.
│   │   │   ├── __init__.py       # Initializes the API models package.
│   │   │   ├── auth.py           # Pydantic models for all authentication-related API endpoints.
│   │   │   ├── common.py         # Common Pydantic models for standardized API responses (e.g., Success, Error).
│   │   │   └── tenant_settings.py # Pydantic models for tenant settings API requests and responses.
│   │   ├── router.py             # Top-level API router that aggregates versioned routers.
│   │   └── v1/                   # Contains all code for version 1 of the API.
│   │       ├── __init__.py       # Initializes the 'v1' API package.
│   │       ├── agents/           # API endpoints related to AI agents.
│   │       │   ├── __init__.py   # Initializes the 'agents' API package.
│   │       │   ├── router.py     # FastAPI router for agent catalog and status endpoints.
│   │       │   └── schemas.py    # Pydantic schemas for agent-related API models.
│   │       ├── auth/             # API endpoints for all authentication and authorization flows.
│   │       │   ├── __init__.py   # Initializes the 'auth' API package.
│   │       │   ├── router.py     # Aggregates all individual authentication-related routers.
│   │       │   ├── routes_email.py # API routes for sending and confirming email verifications.
│   │       │   ├── routes_passwords.py # API routes for password management (forgot, reset, change).
│   │       │   ├── routes_service_account_tokens.py # API routes for managing (listing/revoking) service account tokens.
│   │       │   ├── routes_service_accounts.py # API routes for issuing service account tokens.
│   │       │   ├── routes_sessions.py # API routes for user session management (login, logout, refresh, list).
│   │       │   ├── routes_signup.py # API route for public user and tenant registration.
│   │       │   └── utils.py      # Utility functions for the authentication API routes.
│   │       ├── billing/          # API endpoints related to billing and subscriptions.
│   │       │   ├── __init__.py   # Initializes the 'billing' API package.
│   │       │   ├── router.py     # FastAPI router for managing subscriptions, plans, and usage.
│   │       │   └── schemas.py    # Pydantic schemas for billing API requests and responses.
│   │       ├── chat/             # API endpoints for real-time chat with agents.
│   │       │   ├── __init__.py   # Initializes the 'chat' API package.
│   │       │   ├── router.py     # FastAPI router for handling chat and streaming chat requests.
│   │       │   └── schemas.py    # Pydantic schemas for chat requests and responses.
│   │       ├── conversations/    # API endpoints for managing conversation history.
│   │       │   ├── __init__.py   # Initializes the 'conversations' API package.
│   │       │   ├── router.py     # FastAPI router for listing, retrieving, and deleting conversations.
│   │       │   └── schemas.py    # Pydantic schemas for conversation history and summaries.
│   │       ├── router.py         # Top-level router for all v1 API endpoints.
│   │       ├── status/           # API endpoints for platform status and incident reporting.
│   │       │   ├── __init__.py   # Initializes the 'status' API package.
│   │       │   ├── router.py     # FastAPI router for platform status, incidents, and alert subscriptions.
│   │       │   └── schemas.py    # Pydantic schemas for platform status responses.
│   │       ├── tenants/          # API endpoints for tenant-specific management.
│   │       │   ├── __init__.py   # Initializes the 'tenants' API package.
│   │       │   ├── router.py     # Aggregates routers related to tenant management.
│   │       │   └── routes_settings.py # API routes for getting and updating tenant-level settings.
│   │       └── tools/            # API endpoints for inspecting available agent tools.
│   │           ├── __init__.py   # Initializes the 'tools' API package.
│   │           └── router.py     # FastAPI router for listing available agent tools.
│   ├── bootstrap/                # Handles application startup and dependency injection.
│   │   ├── __init__.py           # Exposes the application container and its management functions.
│   │   └── container.py          # Defines the central dependency injection container for application services.
│   ├── cli/                      # Placeholder for command-line interface scripts.
│   │   └── __init__.py           # Initializes the 'cli' package.
│   ├── core/                     # Core application logic, configuration, and security primitives.
│   │   ├── __init__.py           # Initializes the 'core' package.
│   │   ├── config.py             # Defines and manages application settings using Pydantic.
│   │   ├── keys.py               # Shim re-exporting shared cryptographic key management utilities.
│   │   ├── password_policy.py    # Defines and validates password strength policies.
│   │   ├── security.py           # Handles JWT creation/validation, password hashing, and token signing.
│   │   ├── service_accounts.py   # Defines and loads the catalog of available service accounts.
│   │   └── service_accounts.yaml # YAML data file defining service accounts, their scopes, and TTLs.
│   ├── domain/                   # Contains business logic, entities, and repository interfaces (contracts).
│   │   ├── __init__.py           # Initializes the 'domain' package.
│   │   ├── auth.py               # Domain models and repository contracts for authentication concerns.
│   │   ├── billing.py            # Domain models and repository contracts for billing.
│   │   ├── conversations.py      # Domain models and repository contracts for conversations.
│   │   ├── email_verification.py # Domain models and repository contract for email verification tokens.
│   │   ├── password_reset.py     # Domain models and repository contract for password reset tokens.
│   │   ├── status.py             # Domain models and repository contracts for platform status and subscriptions.
│   │   ├── tenant_settings.py    # Domain models and repository contract for tenant settings.
│   │   └── users.py              # Domain models and repository contracts for users and memberships.
│   ├── infrastructure/           # Implements domain repository contracts and integrates with external services.
│   │   ├── __init__.py           # Initializes the 'infrastructure' package.
│   │   ├── db/                   # Database connection and session management.
│   │   │   ├── __init__.py       # Exposes database engine and session helpers.
│   │   │   ├── engine.py         # Manages the global SQLAlchemy async engine and session factory.
│   │   │   └── session.py        # Provides a FastAPI dependency for database sessions.
│   │   ├── notifications/        # Adapters for sending notifications like emails.
│   │   │   ├── __init__.py       # Exposes notification adapters for easy import.
│   │   │   └── resend.py         # Adapter for sending transactional emails via the Resend API.
│   │   ├── openai/               # Integration with the OpenAI SDK and services.
│   │   │   ├── __init__.py       # Initializes the OpenAI integration package.
│   │   │   ├── runner.py         # Wrapper around the OpenAI Agents SDK runner.
│   │   │   └── sessions.py       # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK.
│   │   ├── persistence/          # Concrete repository implementations for data storage.
│   │   │   ├── __init__.py       # Initializes the 'persistence' package.
│   │   │   ├── auth/             # Persistence implementations for authentication data.
│   │   │   │   ├── cache.py      # Redis-backed cache for refresh tokens.
│   │   │   │   ├── models.py     # SQLAlchemy ORM models for users, memberships, and tokens.
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository.
│   │   │   │   ├── session_repository.py # Postgres implementation of the user session repository.
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository.
│   │   │   ├── billing/          # Persistence implementations for billing data.
│   │   │   │   ├── __init__.py   # Initializes the billing persistence package.
│   │   │   │   ├── models.py     # SQLAlchemy ORM models for billing plans, subscriptions, and usage.
│   │   │   │   └── postgres.py   # Postgres implementation of the billing repository.
│   │   │   ├── conversations/    # Persistence implementations for conversation data.
│   │   │   │   ├── __init__.py   # Initializes the conversation persistence package.
│   │   │   │   ├── models.py     # SQLAlchemy ORM models for tenants, conversations, and messages.
│   │   │   │   └── postgres.py   # Postgres implementation of the conversation repository.
│   │   │   ├── models/           # Shared base for SQLAlchemy models.
│   │   │   │   └── base.py       # Defines the declarative base and naming conventions for SQLAlchemy.
│   │   │   ├── status/           # Persistence for platform status subscriptions.
│   │   │   │   ├── __init__.py   # Initializes the status persistence package.
│   │   │   │   ├── models.py     # SQLAlchemy ORM model for status subscriptions.
│   │   │   │   ├── postgres.py   # Postgres implementation of the status subscription repository.
│   │   │   │   └── repository.py # Factory function for creating the status subscription repository.
│   │   │   ├── stripe/           # Persistence for Stripe webhook events.
│   │   │   │   ├── models.py     # SQLAlchemy ORM models for storing Stripe events and dispatches.
│   │   │   │   └── repository.py # Repository for creating and querying stored Stripe events.
│   │   │   └── tenants/          # Persistence for tenant-specific data.
│   │   │       ├── __init__.py   # Initializes the tenant persistence package.
│   │   │       ├── models.py     # SQLAlchemy ORM model for tenant settings.
│   │   │       └── postgres.py   # Postgres implementation of the tenant settings repository.
│   │   ├── security/             # Implementations of security-related contracts.
│   │   │   ├── cipher.py         # Utilities for symmetric encryption using cryptography.fernet.
│   │   │   ├── email_verification_store.py # Redis implementation of the email verification token store.
│   │   │   ├── nonce_store.py    # Redis implementation of a nonce store for replay protection.
│   │   │   ├── password_reset_store.py # Redis implementation of the password reset token store.
│   │   │   ├── vault.py          # Client for interacting with HashiCorp Vault's Transit engine.
│   │   │   └── vault_kv.py       # Re-exports shared Vault KV helpers for secret management.
│   │   ├── status/               # Infrastructure for platform status reporting.
│   │   │   ├── __init__.py       # Initializes the status infrastructure package.
│   │   │   └── repository.py     # In-memory implementation of the platform status repository.
│   │   └── stripe/               # Stripe API client and helpers.
│   │       ├── __init__.py       # Exposes the Stripe client and related data classes.
│   │       ├── client.py         # A typed client wrapper for interacting with the Stripe API.
│   │       └── types.py          # Typing helpers and wrappers for the dynamic Stripe SDK.
│   ├── middleware/               # Custom FastAPI middleware.
│   │   ├── __init__.py           # Initializes the 'middleware' package.
│   │   └── logging.py            # Middleware for logging HTTP requests and responses with correlation IDs.
│   ├── observability/            # Code related to logging, metrics, and tracing.
│   │   ├── __init__.py           # Initializes the observability package.
│   │   ├── logging.py            # Helper for structured JSON event logging.
│   │   └── metrics.py            # Defines and configures Prometheus metrics.
│   ├── presentation/             # Handles data presentation to external systems (e.g., webhooks, emails).
│   │   ├── __init__.py           # Initializes the 'presentation' package.
│   │   ├── emails/               # Email template rendering.
│   │   │   ├── __init__.py       # Exposes email template renderers.
│   │   │   └── templates.py      # Renders HTML and plain text for transactional emails.
│   │   ├── health.py             # FastAPI router for liveness and readiness health checks.
│   │   ├── metrics.py            # FastAPI router for the Prometheus metrics scrape endpoint.
│   │   ├── webhooks/             # Handlers for incoming webhooks from external services.
│   │   │   ├── __init__.py       # Initializes the 'webhooks' package.
│   │   │   └── stripe.py         # FastAPI router for handling incoming Stripe webhooks.
│   │   └── well_known.py         # FastAPI router for /.well-known endpoints (e.g., jwks.json).
│   ├── services/                 # Application services that orchestrate domain logic.
│   │   ├── __init__.py           # Initializes the 'services' package.
│   │   ├── agent_service.py      # Core service for orchestrating AI agent interactions and tools.
│   │   ├── auth/                 # Specialized sub-services for authentication and authorization.
│   │   │   ├── __init__.py       # Exposes auth sub-service components.
│   │   │   ├── builders.py       # Factory functions for building various authentication services.
│   │   │   ├── errors.py         # Custom error types for authentication services.
│   │   │   ├── refresh_token_manager.py # Manages the lifecycle and storage of refresh tokens.
│   │   │   ├── service_account_service.py # Service for issuing and managing service account tokens.
│   │   │   ├── session_service.py # Service for managing human user sessions (login, refresh, logout).
│   │   │   └── session_store.py  # High-level helper for persisting user session metadata with GeoIP.
│   │   ├── auth_service.py       # Façade that aggregates various authentication sub-services.
│   │   ├── billing_events.py     # Service for broadcasting billing events to subscribers via Redis streams.
│   │   ├── billing_service.py    # Service for managing billing plans and subscriptions via a payment gateway.
│   │   ├── conversation_service.py # Service for managing and searching conversation histories.
│   │   ├── email_verification_service.py # Service for orchestrating the email verification flow.
│   │   ├── geoip_service.py      # Pluggable service for IP-based geolocation lookups.
│   │   ├── password_recovery_service.py # Service for handling the password recovery (forgot password) flow.
│   │   ├── payment_gateway.py    # Abstraction for a payment provider, with a Stripe implementation.
│   │   ├── rate_limit_service.py # Redis-backed service for rate limiting API requests.
│   │   ├── service_account_bridge.py # Bridges browser-based requests to the service account issuance flow.
│   │   ├── signup_service.py     # Service for orchestrating new user and tenant registration.
│   │   ├── status_alert_dispatcher.py # Service for fanning out status incident alerts to subscribers.
│   │   ├── status_service.py     # Service for retrieving platform status snapshots.
│   │   ├── status_subscription_service.py # Service for managing status page alert subscriptions.
│   │   ├── stripe_dispatcher.py  # Service for dispatching Stripe webhook events to appropriate handlers.
│   │   ├── stripe_event_models.py # Shared data classes for Stripe webhook dispatching and event streams.
│   │   ├── stripe_retry_worker.py # Background worker for retrying failed Stripe event dispatches.
│   │   ├── tenant_settings_service.py # Service for managing tenant-specific settings.
│   │   └── user_service.py       # Service for user management, authentication logic, and password policies.
│   └── utils/                    # General utility functions and classes.
│       ├── __init__.py           # Initializes the 'utils' package.
│       ├── tools/                # AI agent tools and their registration mechanism.
│       │   ├── __init__.py       # Exposes the tool registry and specific tools.
│       │   ├── registry.py       # A central registry for managing and organizing agent tools.
│       │   └── web_search.py     # Implements a web search tool using the Tavily API.
│       └── user_agent.py         # Utility for parsing and summarizing User-Agent strings.
├── main.py                     # Main FastAPI application entry point, including startup/shutdown logic.
├── tests/                      # Contains all automated tests for the application.
│   ├── __init__.py             # Initializes the 'tests' package.
│   ├── conftest.py               # Shared pytest fixtures for dependency mocking and test setup.
│   ├── contract/                 # Tests for API contracts and external-facing boundaries.
│   │   ├── __init__.py           # Initializes the 'contract' test package.
│   │   ├── test_agents_api.py    # Contract tests for the agent, chat, and conversation APIs.
│   │   ├── test_auth_service_account_tokens.py # Contract tests for service account token management APIs.
│   │   ├── test_auth_service_accounts.py # Contract tests for CLI-based service account token issuance.
│   │   ├── test_auth_service_accounts_browser.py # Contract tests for browser-based service account token issuance.
│   │   ├── test_auth_users.py    # Contract tests for human user authentication and session APIs.
│   │   ├── test_health_endpoints.py # Contract tests for the health check endpoints.
│   │   ├── test_metrics_endpoint.py # Contract test for the Prometheus metrics endpoint.
│   │   ├── test_status_api.py    # Contract tests for the public platform status API.
│   │   ├── test_streaming_manual.py # Manual test script for verifying Server-Sent Events (SSE) streaming.
│   │   ├── test_tenant_settings.py # Contract tests for the tenant settings API.
│   │   └── test_well_known.py    # Contract tests for the /.well-known/jwks.json endpoint.
│   ├── fixtures/                 # Contains test data files and fixtures.
│   │   ├── keysets               # Directory for test cryptographic keysets.
│   │   └── stripe                # Directory for Stripe webhook event fixture JSON files.
│   ├── integration/              # Tests requiring external resources like a real database.
│   │   ├── __init__.py           # Initializes the 'integration' test package.
│   │   ├── test_billing_stream.py # Integration tests for the billing Server-Sent Events (SSE) stream.
│   │   ├── test_postgres_migrations.py # Integration tests to verify database migrations against a real Postgres DB.
│   │   ├── test_stripe_replay_cli.py # Integration tests for the Stripe event replay CLI tool.
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook handler.
│   ├── unit/                     # Fast, isolated unit tests with mocks and fakes.
│   │   ├── api/                  # Unit tests for the API layer.
│   │   │   └── test_routes_service_account_tokens.py # Unit tests for service account token route logic.
│   │   ├── test_auth_domain.py   # Unit tests for auth domain helpers (e.g., token hashing).
│   │   ├── test_auth_service.py  # Unit tests for the main authentication service facade.
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault claim validation logic.
│   │   ├── test_billing_events.py # Unit tests for the billing events service.
│   │   ├── test_billing_service.py # Unit tests for the billing service logic.
│   │   ├── test_cli_forbidden_imports.py # Ensures CLI modules do not import backend code.
│   │   ├── test_cli_imports.py   # Unit tests for CLI module import behavior.
│   │   ├── test_cli_main.py      # Unit tests for the main CLI entrypoint.
│   │   ├── test_config.py        # Unit tests for the application configuration settings class.
│   │   ├── test_email_templates.py # Unit tests for email template rendering logic.
│   │   ├── test_email_verification_service.py # Unit tests for the email verification service.
│   │   ├── test_keys.py          # Unit tests for key management and JWKS generation.
│   │   ├── test_keys_cli.py      # Unit tests for the key management CLI commands.
│   │   ├── test_metrics.py       # Unit tests for Prometheus metrics helpers.
│   │   ├── test_nonce_store.py   # Unit tests for the nonce store used for replay protection.
│   │   ├── test_password_recovery_service.py # Unit tests for the password recovery service.
│   │   ├── test_rate_limit_service.py # Unit tests for the rate limiting service.
│   │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository's logic.
│   │   ├── test_resend_adapter.py # Unit tests for the Resend email adapter.
│   │   ├── test_scope_dependencies.py # Unit tests for FastAPI scope dependency helpers.
│   │   ├── test_secret_guard.py  # Unit tests for production secret enforcement.
│   │   ├── test_security.py      # Unit tests for security utilities like JWT signing/verification.
│   │   ├── test_service_account_bridge.py # Unit tests for the service account browser issuance bridge.
│   │   ├── test_service_account_token_service.py # Unit tests for the service account token issuance service.
│   │   ├── test_setup_inputs.py  # Unit tests for the CLI setup wizard input providers.
│   │   ├── test_setup_validators.py # Unit tests for the CLI setup wizard input validators.
│   │   ├── test_setup_wizard.py  # Unit tests for the CLI setup wizard logic.
│   │   ├── test_signup_service.py # Unit tests for the user and tenant signup service.
│   │   ├── test_stripe_dispatcher.py # Unit tests for the Stripe event dispatcher logic.
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event repository.
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter.
│   │   ├── test_stripe_retry_worker.py # Unit tests for the Stripe dispatch retry worker.
│   │   ├── test_tenant_dependency.py # Unit tests for the tenant context FastAPI dependency.
│   │   ├── test_tenant_settings_service.py # Unit tests for the tenant settings service.
│   │   ├── test_tools.py         # Unit tests for the agent tool registry and tools.
│   │   ├── test_user_models.py   # Unit tests for user-related SQLAlchemy ORM models.
│   │   ├── test_user_repository.py # Unit tests for the user repository implementation.
│   │   ├── test_user_service.py  # Unit tests for the user service logic.
│   │   ├── test_vault_client.py  # Unit tests for the Vault Transit client.
│   │   └── test_vault_kv.py      # Unit tests for the Vault KV client adapter.
│   └── utils/                    # Utility functions and classes for tests.
│       ├── fake_billing_backend.py # A fake billing event backend for testing SSE streams.
│       └── sqlalchemy.py         # SQLAlchemy helper functions for tests.
└── var/                        # Directory for variable data like generated keys.
    └── keys/                   # Default location for storing cryptographic keys on the filesystem.