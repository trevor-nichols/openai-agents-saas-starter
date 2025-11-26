<!-- SECTION: Title -->
# Vector Stores + File Search Milestone — AI-001

_Last updated: November 25, 2025_

## Objective
Add first-class OpenAI vector store + file_search support across the SaaS starter: tenant-scoped storage, CRUD + search APIs, agent/runtime wiring, quotas, and observability, keeping architecture clean and extensible for downstream forks.

## Scope & Current Risks
| Area | Status | Notes |
| --- | --- | --- |
| Data model & migrations | ✅ In repo | Added Alembic revision 20251125_140000 creating vector_stores, vector_store_files, agent_vector_stores.
| Service layer (OpenAI orchestration) | ✅ Complete | ORM models + VectorStoreService (create/attach/search/delete, ensure_primary, soft delete) with tenant-aware OpenAI client hook.
| API surface (tenant-scoped CRUD + search) | ✅ In repo | Added `/api/v1/vector-stores` CRUD, files attach/list/get/delete, search proxy with tenant role enforcement.
| Agent integration (FileSearch tool + bindings) | Deferred | Will decide per-agent strategy in a follow-up milestone; no wiring shipped yet.
| Docs & how-to (API + agent patterns) | ✅ In repo | Runbook documents ingestion, search, tenant-default binding patterns, plan overrides, and sync worker toggles.
| Quotas, security, observability | ✅ In repo | Size/MIME/store/file caps, metrics/logging, tracing spans on create/attach/search/delete; plan-aware overrides when billing entitlements supplied.
| Background sync/expiry (phase 2) | ✅ In repo | Worker refreshes store/file status and enforces expiry; on by default (can be disabled).

## Execution Plan
1. **Schema & migration** — Add tables/enums, indexes, constraints; keep SQLite compatibility (CITEXTCompat/JSONBCompat).
2. **Service layer** — Implement `VectorStoreService` wrapping OpenAI vector store/file/search calls; enforce MIME/size/plan limits; tenant API key selection; soft-delete handling.
3. **API endpoints** — Tenant-auth routes for store CRUD, file attach/list/get/delete, and search proxy; request/response schemas; error handling aligned to OpenAI constraints.
4. **Agent wiring** — Register FileSearchTool; extend AgentSpec (binding, vector_store_ids, file_search_options); runtime resolver to inject tenant/default store IDs; validation to fail fast when unresolved.
5. **Quotas & observability** — Add plan-based limits, metrics (ingestion/search latency, bytes, counts), structured logs with request IDs; optional feature flag to auto-create primary store per tenant.
6. **Docs & examples** — Update runbooks, tool catalog, agent README; add example script mirroring `vector_store.py`; document API usage.
7. **Background sync (optional)** — Periodic refresh of in-progress files/stores and expiry cleanup.
8. **Testing** — Unit mocks for OpenAI, integration happy-path with SQLite, agent build validation, schema/validation tests, example fixture data.
9. **Closeout** — Update ISSUE_TRACKER, CLI inventory if needed, move tracker to `complete/` with sign-off.

## Deliverables
- Alembic migration creating vector store tables + enums.
- `VectorStoreService` with OpenAI client integration and guardrails.
- Tenant-scoped API routes for stores, files, and search with Pydantic schemas.
- Tool registry + AgentSpec/runtime updates enabling FileSearch + tenant/default binding.
- Quota enforcement + observability instrumentation.
- Documentation and code examples demonstrating ingestion and search.
- Test coverage for API/service/schema/agent wiring.

## Changelog
- **2025-11-25**: Milestone drafted; scope, plan, and deliverables recorded.
- **2025-11-25**: Phase I started — added Alembic revision 20251125_140000 for vector_stores, vector_store_files, agent_vector_stores.
- **2025-11-25**: Phase II complete — added ORM models and VectorStoreService (create/attach/search/delete/ensure_primary/soft-delete) with tenant-aware OpenAI client hook.
- **2025-11-25**: Phase III in progress — exposed `/api/v1/vector-stores` CRUD/files/search routes with tenant role checks and Pydantic schemas.
- **2025-11-25**: Container wiring — VectorStoreService registered during app lifespan using shared session factory + settings.
- **2025-11-25**: Added guardrails (size/MIME/store/file caps, quota errors) and metrics/logging around vector store operations; tracing still pending.
- **2025-11-25**: Added tracing spans on create/attach/search/delete and unit tests for quota/mime/dup-name guardrails.
- **2025-11-25**: Added plan-aware vector limits (optional billing entitlements), sync worker toggle, CLI wizard support, and docs on overrides/expiry.
- **2025-11-25**: Agent integration deferred; will be scoped once agent/tool strategy is defined. Docs updated with how-to patterns for future wiring.

## Sign-off
- **Owner**: @codex
- **Date**: November 26, 2025
- **Summary**: Vector stores + file search shipped: schema/migrations, service + quota guardrails, tenant CRUD/files/search APIs, sync worker with expiry/purge, docs/runbook. Agent integration intentionally deferred to next milestone.
