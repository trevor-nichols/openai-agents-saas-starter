## Backend Issue Tracker

| ID | Title | Description | Status | Owner | Notes |
|----|-------|-------------|--------|-------|-------|
| BE-001 | SSE stream endpoint mismatch | Frontend streams against `/api/v1/agents/chat/stream` while FastAPI exposes `/api/v1/chat/stream`, breaking real-time updates. | Resolved | – | Frontend + smoke test now target `/api/v1/chat/stream`. |
| BE-002 | Conversation history is in-memory only | `InMemoryConversationRepository` is the default and no durable adapter exists, so conversations evaporate on restart / multi-instance deploys. | In Progress | – | Postgres repository wired via `use_in_memory_repo=false`; need migration-powered rollout + durability tests. |
| BE-003 | Tool registry lacks agent-specific scoping | `ToolRegistry.get_core_tools()` returns the same tool set for every agent, preventing specialization as catalog grows. | Open | – | Extend registry to support per-agent tool bundles and metadata-driven assignment. |
| BE-004 | Authentication is demo-only | `/api/v1/auth` hard-codes demo credentials and issues JWTs without user store or hashing pipeline. | Open | – | Replace with real identity provider or disable in prod builds. |
| BE-005 | Multi-agent handoff not configured | `AgentRegistry` provisions specialized agents but never wires `handoffs`, so triage cannot delegate per SDK guidance. | Resolved | – | Triage agent now uses SDK `handoff(...)` with prompt helper and descriptions. |
| DB-001 | Durable conversation schema & migrations | Introduce SQLAlchemy models plus Alembic migration for Postgres conversation/billing tables. | In Progress | – | Alembic scaffold + baseline migration `20251106_120000`; CI smoke tests exercise upgrade/downgrade on Postgres. |
| DB-002 | Async engine bootstrap & configuration | Add Postgres engine/session factory, settings, startup validation, and local tooling support. | In Progress | – | Async engine + health check implemented; document Docker workflow and production toggles. |
| DB-003 | Conversation repository integration | Implement Postgres-backed repository, wire into agent service, and update tests/tooling. | In Progress | – | Repository live with CI coverage (`tests/integration/test_postgres_migrations.py`); next: metrics + retention hooks. |
| BILL-001 | Billing service & API scaffolding | Deliver tenant-scoped billing commands (start/update/cancel/usage) with role guards and Stripe-ready hooks. | In Progress | – | Endpoints exposed under `/api/v1/billing`, Postgres repository & gateway stubs implemented; pending Stripe integration & webhook handling. |
