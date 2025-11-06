# Milestone: Durable Conversations & Billing Scaffold

## Objective
- Replace the in-memory conversation store with a production-grade PostgreSQL + SQLAlchemy implementation.
- Seed billing primitives so the application can evolve into a multi-tenant SaaS with plan and usage awareness.

## Architecture Decisions (2025-11-06)
- **Persistence Layer**: Async SQLAlchemy models + repositories under `app/infrastructure/persistence` with a shared async engine manager.
- **Domain Contracts**: Keep existing `ConversationRepository` protocol; introduce discrete services for conversations and billing that are injected into `AgentService`.
- **Database Schema**:
  - Conversations: `tenant_accounts`, `users`, `agent_conversations`, `agent_messages`.
  - Billing: `billing_plans`, `plan_features`, `tenant_subscriptions`, `subscription_invoices`, `subscription_usage`.
- **Configuration**: New settings (`database_url`, pool sizing, feature flags). Application startup must fail fast if durable storage is required but unreachable.
- **Observability**: Extended health checks, structured logging around persistence, OpenTelemetry counters for conversation and subscription events.

## Work Breakdown

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| DB-001 | Schema & Migrations | Define SQLAlchemy models and Alembic migrations for conversation + billing tables. | – | In Progress |
| DB-002 | Engine Bootstrap | Implement async engine/session factory, settings, and startup validation (with Docker compose profile). | – | In Progress |
| DB-003 | Conversation Repository | Create PostgreSQL-backed repository + service adapter, wire into `AgentService`, update tests. | – | In Progress |
| DB-004 | SDK Session Integration | Align chat flows with Agents SDK session memory to leverage persistent history. | – | Planned |
| DB-005 | Billing Service Scaffold | Implement plan catalog, subscription service, usage recording stubs, and unit tests. | – | Planned |
| DB-006 | API & Health | Add health probes for storage, document new endpoints/config, update README. | – | Planned |

## Notes & Assumptions
- PostgreSQL 15+ is the reference target; leverage UUID primary keys and JSONB columns.
- Redis remains available for caching conversation summaries and rate limiting, but is not the source of truth.
- Stripe or other processors are out of scope; billing tables must be generic and safe for future integration.
- All new components must pass existing lint/type checks and include contract/integration tests using an ephemeral Postgres instance.

## ERD Overview

```
TenantAccount (1) ────< (many) User
      │
      └─────< AgentConversation (many) ────< AgentMessage (many)

TenantAccount (1) ────< TenantSubscription (many) ────< SubscriptionInvoice (many)
                                              └──────< SubscriptionUsage (many)

BillingPlan (1) ────< PlanFeature (many)
BillingPlan (1) ────< TenantSubscription (many)
```

### Table Attributes (key fields only)
- **tenant_accounts**: `id (UUID PK)`, `slug`, `name`, `created_at`.
- **users**: `id (UUID PK)`, `tenant_id FK`, `external_id`, `display_name`, `created_at`.
- **agent_conversations**: `id (UUID PK)`, `tenant_id FK`, `user_id FK`, `agent_entrypoint`, `active_agent`, `status`, `message_count`, `total_tokens_prompt`, `total_tokens_completion`, `reasoning_tokens`, `handoff_count`, `source_channel`, `topic_hint`, `last_message_at`, `created_at`, `updated_at`.
- **agent_messages**: `id (bigserial PK)`, `conversation_id FK`, `position`, `role`, `agent_type`, `content (JSONB)`, `tool_name`, `tool_call_id`, `token_count_prompt`, `token_count_completion`, `reasoning_tokens`, `latency_ms`, `content_checksum`, `created_at`.
- **billing_plans**: `id (UUID PK)`, `code`, `name`, `interval`, `interval_count`, `price_cents`, `currency`, `trial_days`, `seat_included`, `feature_toggles (JSONB)`, `is_active`, timestamps.
- **plan_features**: `id (bigserial PK)`, `plan_id FK`, `feature_key`, `display_name`, `hard_limit`, `soft_limit`, `is_metered`, `created_at`.
- **tenant_subscriptions**: `id (UUID PK)`, `tenant_id FK`, `plan_id FK`, `status`, `auto_renew`, `billing_email`, `starts_at`, `current_period_start/end`, `trial_ends_at`, `cancel_at`, `seat_count`, `metadata_json (JSONB)`, timestamps.
- **subscription_invoices**: `id (UUID PK)`, `subscription_id FK`, `period_start`, `period_end`, `amount_cents`, `currency`, `status`, `external_invoice_id`, `hosted_invoice_url`, `created_at`.
- **subscription_usage**: `id (UUID PK)`, `subscription_id FK`, `feature_key`, `unit`, `period_start`, `period_end`, `quantity`, `reported_at`, `external_event_id`.

## Execution Plan

### DB-001 — Schema & Migrations
1. Finalise SQLAlchemy model definitions covering all conversation and billing tables (including indices and constraints).
2. Scaffold Alembic environment (if not present) with async-compatible configuration and naming conventions.
3. Generate initial migration `20251106_create_conversation_and_billing_tables` and review for idempotency.
4. Add migration tests/integration checks using ephemeral Postgres (e.g., pytest fixture that runs `alembic upgrade head`).
5. Update developer tooling (Makefile task or hatch script) to run migrations locally and in CI.

### DB-002 — Engine Bootstrap
1. Extend `Settings` with `database_url`, pool sizing, and feature toggles (`use_in_memory_repo`, `enable_billing`).
2. Implement async engine/session factory module providing `async_sessionmaker` and dependency-injected Unit of Work helpers.
3. Add application startup hook to validate connectivity and run pending migrations in development mode (optional toggle).
4. Provide Docker Compose profile for Postgres (and Redis) plus `.env.example` guidance.
5. Backfill health checks (`/health/storage`) and observability hooks (structured logs, metrics) for database availability.

## Progress Log
- **2025-11-06**: Alembic scaffolded under `anything-agents/alembic`, baseline migration `20251106_120000_create_conversation_and_billing_tables.py` authored with seeded Starter/Pro plans.
- **2025-11-06**: Async engine bootstrap added (`app/infrastructure/db`), new settings for database configuration, and readiness health check now verifies Postgres connectivity.
- **2025-11-06**: Implemented Postgres conversation repository (`app/infrastructure/persistence/conversations/postgres.py`), updated agent service for async persistence, and adjusted tests + routes to await new interfaces.
- **2025-11-06**: Added CI-backed Postgres smoke tests (`tests/integration/test_postgres_migrations.py`) and GitHub Actions workflow service wiring to validate migrations on every PR.
- **2025-11-06**: Replaced billing in-memory adapter with Postgres-backed repository and gated wiring through `ENABLE_BILLING` in `main.py`.
- **2025-11-06**: Delivered tenant-scoped billing endpoints (start/update/cancel/usage), tenant role guards, and unit/integration coverage for updates and usage reporting.

## Next Actions
1. Document Docker Compose workflow and local developer guidance for running Postgres integration suite.
2. Flesh out billing service scaffolding once repository wiring is complete (DB-005).
3. Implement retention policies and usage analytics leveraging the new persistence layer.
