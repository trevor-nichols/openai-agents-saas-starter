.
├── .pytest_cache/                                # Cache directory for pytest runs
│   ├── CACHEDIR.TAG                              # Pytest cache directory tag file
│   └── v/                                        # Directory for pytest cache data
├── alembic/                                      # Alembic database migration configuration and scripts
│   ├── env.py                                    # Alembic runtime environment configuration script
│   ├── script.py.mako                            # Mako template for generating new migration scripts
│   ├── versions/                                 # Contains individual database migration scripts
│   │   ├── 20251106_120000_create_conversation_and_billing_tables.py # Initial migration for conversation and billing tables
│   │   ├── 20251106_220000_add_service_account_tokens.py # Migration to add service account refresh token table
│   │   ├── 20251106_230500_hash_refresh_token_column.py # Migration to hash the refresh token column for security
│   │   ├── 20251106_235500_add_signing_kid_column.py # Migration to add a key ID for signing refresh tokens
│   │   └── __init__.py                           # Initializes the versions directory as a Python package
├── alembic.ini                                   # Configuration file for Alembic database migrations
├── app/                                          # Main application source code
│   ├── __init__.py                               # Initializes the 'app' package
│   ├── api/                                      # API layer containing routers, models, and dependencies
│   │   ├── __init__.py                           # Initializes the 'api' package
│   │   ├── dependencies/                         # FastAPI dependency injection helpers
│   │   │   ├── __init__.py                       # Exposes shared dependency helpers
│   │   │   ├── auth.py                           # Authentication-related dependency functions
│   │   │   ├── common.py                         # Common dependency functions like pagination
│   │   │   └── tenant.py                         # Dependencies for handling multi-tenancy context
│   │   ├── errors.py                             # Centralized API exception handlers
│   │   ├── models/                               # Pydantic models for API request/response validation
│   │   │   ├── __init__.py                       # Initializes the 'models' package
│   │   │   ├── auth.py                           # Pydantic models for authentication and tokens
│   │   │   └── common.py                         # Common API response models (Success, Error, etc.)
│   │   ├── router.py                             # Top-level API router aggregating versioned routers
│   │   └── v1/                                   # Code for version 1 of the API
│   │       ├── __init__.py                       # Initializes the 'v1' API package
│   │       ├── agents/                           # API endpoints for agent management
│   │       │   ├── __init__.py                   # Initializes the 'agents' API package
│   │       │   ├── router.py                     # FastAPI router for `/agents` endpoints
│   │       │   └── schemas.py                    # Pydantic schemas for agent-related API responses
│   │       ├── auth/                             # API endpoints for authentication
│   │       │   ├── __init__.py                   # Initializes the 'auth' API package
│   │       │   └── router.py                     # FastAPI router for `/auth` (token, service accounts)
│   │       ├── billing/                          # API endpoints for billing and subscriptions
│   │       │   ├── __init__.py                   # Initializes the 'billing' API package
│   │       │   ├── router.py                     # FastAPI router for `/billing` endpoints
│   │       │   └── schemas.py                    # Pydantic schemas for billing API requests and responses
│   │       ├── chat/                             # API endpoints for chat interactions
│   │       │   ├── __init__.py                   # Initializes the 'chat' API package
│   │       │   ├── router.py                     # FastAPI router for `/chat` endpoints, including streaming
│   │       │   └── schemas.py                    # Pydantic schemas for chat requests and responses
│   │       ├── conversations/                    # API endpoints for managing conversation history
│   │       │   ├── __init__.py                   # Initializes the 'conversations' API package
│   │       │   ├── router.py                     # FastAPI router for `/conversations` endpoints
│   │       │   └── schemas.py                    # Pydantic schemas for conversation history and summaries
│   │       ├── router.py                         # Aggregates all routers for the v1 API
│   │       └── tools/                            # API endpoints for listing agent tools
│   │           ├── __init__.py                   # Initializes the 'tools' API package
│   │           └── router.py                     # FastAPI router for the `/tools` endpoint
│   ├── cli/                                      # Command-line interface scripts
│   │   ├── __init__.py                           # Initializes the 'cli' package
│   │   └── auth_cli.py                           # CLI for auth tasks like issuing service account tokens
│   ├── core/                                     # Core application logic, configuration, and security
│   │   ├── __init__.py                           # Initializes the 'core' package
│   │   ├── config.py                             # Pydantic-based application settings management
│   │   ├── keys.py                               # Management of signing key lifecycle (generation, storage, rotation)
│   │   ├── security.py                           # JWT, password hashing, and token signing/verification logic
│   │   ├── service_accounts.py                   # Loads and manages service account definitions from YAML
│   │   └── service_accounts.yaml                 # Defines available service accounts and their permissions
│   ├── domain/                                   # Core business models and repository interfaces (protocols)
│   │   ├── __init__.py                           # Initializes the 'domain' package
│   │   ├── auth.py                               # Domain models and repository protocol for authentication
│   │   ├── billing.py                            # Domain models and repository protocol for billing
│   │   └── conversations.py                      # Domain models and repository protocol for conversations
│   ├── infrastructure/                           # Implementation of external services (DB, APIs, etc.)
│   │   ├── __init__.py                           # Initializes the 'infrastructure' package
│   │   ├── db/                                   # Database connection management
│   │   │   ├── __init__.py                       # Exposes key database management functions
│   │   │   ├── engine.py                         # Manages the async SQLAlchemy engine and session factory
│   │   │   └── session.py                        # FastAPI dependency for providing database sessions
│   │   ├── openai/                               # Wrappers for the OpenAI SDK
│   │   │   ├── __init__.py                       # Initializes the 'openai' package
│   │   │   └── runner.py                         # Wrapper for executing OpenAI agent runs
│   │   ├── persistence/                          # Implementations of the domain repository protocols
│   │   │   ├── __init__.py                       # Initializes the 'persistence' package
│   │   │   ├── auth/                             # Persistence logic for authentication data
│   │   │   │   ├── cache.py                      # Redis-backed cache for refresh tokens
│   │   │   │   ├── models.py                     # SQLAlchemy ORM model for service account tokens
│   │   │   │   └── repository.py                 # Postgres implementation of the refresh token repository
│   │   │   ├── billing/                          # Persistence logic for billing data
│   │   │   │   ├── __init__.py                   # Exposes billing repository implementations
│   │   │   │   ├── in_memory.py                  # In-memory billing repository for testing/dev
│   │   │   │   └── postgres.py                   # Postgres implementation of the billing repository
│   │   │   ├── conversations/                    # Persistence logic for conversation data
│   │   │   │   ├── __init__.py                   # Exposes conversation repository implementations
│   │   │   │   ├── in_memory.py                  # In-memory conversation repository for testing/dev
│   │   │   │   ├── models.py                     # SQLAlchemy ORM models for conversations and billing
│   │   │   │   └── postgres.py                   # Postgres implementation of the conversation repository
│   │   │   └── models/                           # Shared persistence components
│   │   │       └── base.py                       # SQLAlchemy declarative base and helpers
│   │   └── security/                             # Security-related infrastructure components
│   │       ├── nonce_store.py                    # Replay-attack protection using nonces (Redis or in-memory)
│   │       ├── vault.py                          # Client for HashiCorp Vault Transit engine
│   │       └── vault_kv.py                       # Client for HashiCorp Vault KV secret store
│   ├── middleware/                               # Custom FastAPI middleware
│   │   ├── __init__.py                           # Initializes the 'middleware' package
│   │   └── logging.py                            # Middleware for request/response logging
│   ├── observability/                            # Code for monitoring and observability
│   │   ├── __init__.py                           # Initializes the 'observability' package
│   │   └── metrics.py                            # Prometheus metric definitions
│   ├── presentation/                             # Non-API, user-facing HTTP endpoints
│   │   ├── __init__.py                           # Initializes the 'presentation' package
│   │   ├── health.py                             # Implements /health and /ready endpoints
│   │   └── well_known.py                         # Implements /.well-known/jwks.json endpoint for JWT keys
│   ├── services/                                 # High-level business services orchestrating domain logic
│   │   ├── __init__.py                           # Initializes the 'services' package
│   │   ├── agent_service.py                      # Core service for orchestrating agent chats
│   │   ├── auth_service.py                       # Service for issuing and managing service account tokens
│   │   ├── billing_service.py                    # Service for managing subscriptions and billing
│   │   ├── conversation_service.py               # Service layer for managing conversation data
│   │   └── payment_gateway.py                    # Abstraction for payment processors like Stripe
│   └── utils/                                    # General utility functions and classes
│       ├── __init__.py                           # Initializes the 'utils' package
│       └── tools/                                # Agent tool definitions and registry
│           ├── __init__.py                       # Exposes tool registry components
│           ├── registry.py                       # A central registry for managing agent tools
│           └── web_search.py                     # Defines a web search tool using the Tavily API
├── main.py                                       # FastAPI application entry point and configuration
└── tests/                                        # Application test suite
    ├── __init__.py                               # Initializes the 'tests' package
    ├── conftest.py                               # Shared pytest fixtures for all tests
    ├── contract/                                 # API contract tests using a test client
    │   ├── test_agents_api.py                    # Tests for the /agents and /chat API endpoints
    │   ├── test_auth_service_accounts.py         # Tests for the service account issuance flow
    │   ├── test_health_endpoints.py              # Tests for the /health and /ready endpoints
    │   ├── test_streaming_manual.py              # Manual test script for verifying SSE streaming
    │   └── test_well_known.py                    # Tests for the /.well-known/jwks.json endpoint
    ├── fixtures/                                 # Contains test data and fixtures
    │   └── keysets/                              # Directory for test JSON Web Key Sets
    ├── integration/                              # Tests requiring external services (e.g., database)
    │   ├── __init__.py                           # Initializes the 'integration' tests package
    │   └── test_postgres_migrations.py           # Integration tests for Alembic migrations and repositories
    └── unit/                                     # Fast, isolated unit tests with mocks
        ├── test_auth_domain.py                   # Unit tests for authentication domain helpers
        ├── test_auth_service.py                  # Unit tests for the authentication service logic
        ├── test_billing_service.py               # Unit tests for the billing service logic
        ├── test_config.py                        # Unit tests for application settings validation
        ├── test_keys.py                          # Unit tests for cryptographic key management logic
        ├── test_keys_cli.py                      # Unit tests for the key management CLI
        ├── test_nonce_store.py                   # Unit tests for the nonce store replay protection
        ├── test_security.py                      # Unit tests for token signing and verification
        ├── test_tools.py                         # Unit tests for the agent tool registry
        ├── test_vault_client.py                  # Unit tests for the Vault Transit client
        └── test_vault_kv.py                      # Unit tests for the Vault KV secret store client