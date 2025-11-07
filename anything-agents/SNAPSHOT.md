.
├── alembic/                     # Contains Alembic database migration configurations
│   ├── env.py                  # Alembic script to define migration environment and database connection
│   └── script.py.mako          # Mako template for generating new Alembic migration scripts
├── alembic.ini                  # Configuration file for Alembic database migrations
├── app/                         # Main application source code
│   ├── __init__.py             # Initializes the 'app' package
│   ├── api/                     # FastAPI API layer, including routers, models, and dependencies
│   │   ├── __init__.py         # Initializes the 'api' subpackage
│   │   ├── dependencies/        # Reusable FastAPI dependencies for authentication, pagination, etc.
│   │   │   ├── __init__.py     # Exposes shared dependency helpers for convenience
│   │   │   ├── auth.py         # FastAPI dependency to require an authenticated user
│   │   │   ├── common.py       # FastAPI dependency for handling pagination parameters
│   │   │   └── tenant.py       # FastAPI dependencies for multi-tenant context and role enforcement
│   │   ├── errors.py           # Centralized exception handlers for the FastAPI application
│   │   ├── models/             # Pydantic models for API request/response bodies
│   │   │   ├── __init__.py     # Initializes the 'models' subpackage
│   │   │   ├── auth.py         # Pydantic models for authentication requests and responses
│   │   │   └── common.py       # Common Pydantic models for API responses (success, error, pagination)
│   │   ├── router.py           # Top-level API router that includes the versioned (v1) router
│   │   └── v1/                 # Version 1 of the API
│   │       ├── __init__.py     # Initializes the 'v1' API subpackage
│   │       ├── agents/         # API endpoints for managing and interacting with agents
│   │       │   ├── __init__.py # Initializes the 'agents' API subpackage
│   │       │   ├── router.py   # FastAPI router for agent catalog and status endpoints
│   │       │   └── schemas.py  # Pydantic schemas for agent-related API responses
│   │       ├── auth/           # API endpoints for user and service account authentication
│   │       │   ├── __init__.py # Initializes the 'auth' API subpackage
│   │       │   └── router.py   # FastAPI router for user and service account authentication endpoints
│   │       ├── billing/        # API endpoints for billing and subscription management
│   │       │   ├── __init__.py # Initializes the 'billing' API subpackage
│   │       │   ├── router.py   # FastAPI router for billing plans, subscriptions, and usage endpoints
│   │       │   └── schemas.py  # Pydantic schemas for billing-related API requests and responses
│   │       ├── chat/           # API endpoints for chat interactions with agents
│   │       │   ├── __init__.py # Initializes the 'chat' API subpackage
│   │       │   ├── router.py   # FastAPI router for handling chat and streaming chat requests with agents
│   │       │   └── schemas.py  # Pydantic schemas for agent chat requests and responses
│   │       ├── conversations/  # API endpoints for managing conversation history
│   │       │   ├── __init__.py # Initializes the 'conversations' API subpackage
│   │       │   ├── router.py   # FastAPI router for managing conversation history (list, get, delete)
│   │       │   └── schemas.py  # Pydantic models for representing conversation history and summaries
│   │       ├── router.py       # Aggregates all routers for the v1 API
│   │       └── tools/          # API endpoints for listing available agent tools
│   │           ├── __init__.py # Initializes the 'tools' API subpackage
│   │           └── router.py   # FastAPI router for listing available agent tools
│   ├── cli/                     # Command-line interface utilities
│   │   ├── __init__.py         # Initializes the 'cli' package for command-line utilities
│   │   └── auth_cli.py         # Command-line interface for auth tasks like issuing service account tokens
│   ├── core/                    # Core application logic, configuration, and security
│   │   ├── __init__.py         # Initializes the 'core' application package
│   │   ├── config.py           # Defines application settings using Pydantic's `BaseSettings`
│   │   ├── keys.py             # Manages cryptographic keys (Ed25519) for signing tokens
│   │   ├── security.py         # Handles JWT creation/verification and password hashing
│   │   ├── service_accounts.py # Defines and loads service account configurations from YAML
│   │   └── service_accounts.yaml # YAML configuration file defining available service accounts
│   ├── domain/                  # Domain models and business logic contracts (protocols)
│   │   ├── __init__.py         # Initializes the 'domain' package
│   │   ├── auth.py             # Domain models and repository protocols for authentication tokens
│   │   ├── billing.py          # Domain models and repository protocol for billing and subscriptions
│   │   ├── conversations.py    # Domain models and repository protocol for conversation data
│   │   └── users.py            # Domain models and repository protocol for user accounts and memberships
│   ├── infrastructure/          # Adapters for external systems like databases and third-party APIs
│   │   ├── __init__.py         # Initializes the 'infrastructure' package
│   │   ├── db/                 # Database connection and session management
│   │   │   ├── __init__.py     # Exposes database infrastructure helpers
│   │   │   ├── engine.py       # Manages the global SQLAlchemy async engine and session factory
│   │   │   └── session.py      # FastAPI dependency for providing database sessions to routes
│   │   ├── openai/             # Wrappers for the OpenAI Agents SDK
│   │   │   ├── __init__.py     # Initializes the 'openai' infrastructure subpackage
│   │   │   ├── runner.py       # Wrapper around the OpenAI Agents SDK runner for executing agents
│   │   │   └── sessions.py     # Manages SQLAlchemy-backed sessions for the OpenAI Agents SDK
│   │   ├── persistence/        # Data persistence implementations (repositories)
│   │   │   ├── __init__.py     # Initializes the 'persistence' subpackage
│   │   │   ├── auth/           # Persistence layer for authentication data (users, tokens)
│   │   │   │   ├── cache.py    # Redis-backed cache implementation for refresh tokens
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for users, tenants, and tokens
│   │   │   │   ├── repository.py # Postgres implementation of the refresh token repository
│   │   │   │   └── user_repository.py # Postgres implementation of the user repository
│   │   │   ├── billing/        # Persistence layer for billing data
│   │   │   │   ├── __init__.py # Exposes the Postgres billing repository
│   │   │   │   └── postgres.py # Postgres implementation of the billing repository
│   │   │   ├── conversations/  # Persistence layer for conversation data
│   │   │   │   ├── __init__.py # Exposes the Postgres conversation repository
│   │   │   │   ├── models.py   # SQLAlchemy ORM models for conversations, tenants, and billing
│   │   │   │   └── postgres.py # Postgres implementation of the conversation repository
│   │   │   ├── models/         # Shared SQLAlchemy base models
│   │   │   │   └── base.py     # Defines the base declarative class for SQLAlchemy models
│   │   │   └── stripe/         # Persistence layer for Stripe webhook events
│   │   │       ├── models.py   # SQLAlchemy ORM model for storing Stripe webhook events
│   │   │       └── repository.py # Repository for storing and retrieving Stripe webhook events
│   │   ├── security/           # Security-related infrastructure (Vault, nonce store)
│   │   │   ├── nonce_store.py  # Implements a nonce store using Redis for replay protection
│   │   │   ├── vault.py        # Client for HashiCorp Vault's transit engine for signature verification
│   │   │   └── vault_kv.py     # Client for HashiCorp Vault's KV store, used for key storage
│   │   └── stripe/             # Client for interacting with the Stripe API
│   │       ├── __init__.py     # Exposes the Stripe client and its data classes
│   │       └── client.py       # A typed, async-friendly wrapper for the Stripe API client
│   ├── middleware/              # Custom FastAPI middleware
│   │   ├── __init__.py         # Initializes the 'middleware' package
│   │   └── logging.py          # FastAPI middleware for logging requests and responses
│   ├── observability/           # Code for logging, metrics, and tracing
│   │   ├── __init__.py         # Initializes the 'observability' package
│   │   ├── logging.py          # Helper for structured, event-based logging
│   │   └── metrics.py          # Defines and exposes Prometheus metrics for the application
│   ├── presentation/            # Non-API endpoints like health checks and webhooks
│   │   ├── __init__.py         # Initializes the 'presentation' package
│   │   ├── health.py           # Defines `/health` and `/health/ready` endpoints
│   │   ├── metrics.py          # Defines the `/metrics` endpoint for Prometheus scraping
│   │   ├── webhooks/           # Webhook handlers for external services
│   │   │   ├── __init__.py     # Initializes the 'webhooks' presentation subpackage
│   │   │   └── stripe.py       # Defines the webhook endpoint for receiving Stripe events
│   │   └── well_known.py       # Defines the `/.well-known/jwks.json` endpoint
│   ├── services/                # Business logic services that orchestrate components
│   │   ├── __init__.py         # Initializes the 'services' package
│   │   ├── agent_service.py    # Core service for orchestrating agent interactions and managing agents
│   │   ├── auth_service.py     # Service for handling user and service account authentication logic
│   │   ├── billing_events.py   # Service for broadcasting billing events via Redis streams
│   │   ├── billing_service.py  # Service for managing billing plans and subscriptions
│   │   ├── conversation_service.py # Service for managing conversation data and history
│   │   ├── payment_gateway.py  # Abstraction for payment providers, with a Stripe implementation
│   │   └── user_service.py     # Service for user registration, authentication, and lifecycle management
│   └── utils/                   # General utility functions and helpers
│       ├── __init__.py         # Initializes the 'utils' package
│       └── tools/              # Agent tool definitions and registry
│           ├── __init__.py     # Exports tool registry and specific tool implementations
│           ├── registry.py     # Defines a central registry for managing agent tools
│           └── web_search.py   # Implements a web search tool using the Tavily API
├── main.py                      # Main FastAPI application entry point, configuration, and startup logic
├── tests/                       # Contains all tests for the application
│   ├── __init__.py             # Initializes the 'tests' package
│   ├── conftest.py             # Shared pytest fixtures for test setup and configuration
│   ├── contract/                # Tests for API contracts and boundaries
│   │   ├── test_agents_api.py  # Contract tests for the agent-related API endpoints
│   │   ├── test_auth_service_accounts.py # Contract tests for service account token issuance via API/CLI
│   │   ├── test_auth_users.py  # Contract tests for human user authentication API endpoints
│   │   ├── test_health_endpoints.py # Contract tests for the health and readiness check endpoints
│   │   ├── test_metrics_endpoint.py # Contract tests for the Prometheus /metrics endpoint
│   │   ├── test_streaming_manual.py # Manual test script for verifying SSE streaming functionality
│   │   └── test_well_known.py  # Contract tests for the /.well-known/jwks.json endpoint
│   ├── fixtures/                # Test data and fixture files
│   │   ├── keysets/            # Keyset fixtures for testing
│   │   └── stripe/             # Stripe webhook payload fixtures
│   ├── integration/             # Tests requiring external services like a database
│   │   ├── __init__.py         # Initializes the 'integration' test package
│   │   ├── test_billing_stream.py # Integration tests for the server-sent events billing stream
│   │   ├── test_postgres_migrations.py # Integration tests to verify database migrations and repository functionality
│   │   └── test_stripe_webhook.py # Integration tests for the Stripe webhook handler
│   ├── unit/                    # Unit tests for individual components in isolation
│   │   ├── test_auth_domain.py # Unit tests for authentication domain logic (e.g., token hashing)
│   │   ├── test_auth_service.py # Unit tests for the authentication service logic
│   │   ├── test_auth_vault_claims.py # Unit tests for Vault payload claim validation logic
│   │   ├── test_billing_events.py # Unit tests for the billing event broadcasting service
│   │   ├── test_billing_service.py # Unit tests for the billing service logic
│   │   ├── test_config.py      # Unit tests for application settings validation
│   │   ├── test_keys.py        # Unit tests for cryptographic key management logic
│   │   ├── test_keys_cli.py    # Unit tests for the key management command-line interface
│   │   ├── test_metrics.py     # Unit tests for Prometheus metrics helpers
│   │   ├── test_nonce_store.py # Unit tests for the Redis-based nonce store
│   │   ├── test_refresh_token_repository.py # Unit tests for the refresh token repository, especially rehydration
│   │   ├── test_security.py    # Unit tests for token signing and verification
│   │   ├── test_stripe_events.py # Unit tests for the Stripe event repository
│   │   ├── test_stripe_gateway.py # Unit tests for the Stripe payment gateway adapter
│   │   ├── test_tools.py       # Unit tests for the agent tool registry and web search tool
│   │   ├── test_user_models.py # Unit tests for user-related SQLAlchemy model definitions
│   │   ├── test_user_repository.py # Unit tests for the user repository implementation
│   │   ├── test_user_service.py # Unit tests for the user service logic
│   │   ├── test_vault_client.py # Unit tests for the Vault Transit client
│   │   └── test_vault_kv.py    # Unit tests for the Vault KV secret manager client
│   └── utils/                   # Utility helpers for tests
│       └── fake_billing_backend.py # A fake billing event backend for testing purposes
└── var/                         # Variable data, like keys stored on disk
    └── keys/                    # Directory for storing cryptographic keys