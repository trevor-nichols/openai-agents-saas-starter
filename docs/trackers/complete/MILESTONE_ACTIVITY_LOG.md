<!-- SECTION: Metadata -->
# Milestone: Tenant Activity / Audit Log

_Last updated: 2025-12-02_  
**Status:** Complete  
**Owner:** Platform Foundations (@platform-foundations)  
**Domain:** Backend, Cross-cutting  
**ID / Links:** Issue TBD, Design notes in-line

---

<!-- SECTION: Objective -->
## Objective

Deliver a first-class, tenant-scoped audit trail (Activity Log) covering user/system actions across auth, conversations/agents, workflows, billing bridge, and storage/vector operations. Provide REST + optional SSE access, consistent taxonomy, and retention/ops guardrails suitable for production compliance.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- New domain `ActivityEvent` + repository contract with Postgres implementation and migration deployed.
- Activity service with typed helpers; synchronous recording wired into auth, conversations/agents, workflows, billing bridge, storage/vector, and container lifecycle touchpoints.
- API: `GET /api/v1/activity` (filters + cursor pagination) and optional `GET /api/v1/activity/stream` (SSE) with RBAC scope `activity:read` (admins by default).
- Event taxonomy/registry validated at write time; PII handling (IP hash, secret scrubbing) documented and enforced.
- Retention config + cleanup job/script shipped; Prometheus metrics for writes/failures/lag exposed.
- Tests (unit + contract + smoke) green; `hatch run lint`, `hatch run typecheck` pass.
- Docs: backend activity-log doc, tracker updated, changelog entry added.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend audit trail for tenant-scoped actions across auth, conversations/agents, workflows, billing bridge, storage/vector, containers.
- Event taxonomy/registry, validation, and RBAC-protected API/SSE access.
- Retention, metrics, and operational guidance.

### Out of Scope
- Frontend UI surfaces or dashboards (will consume API later).
- Cross-product analytics/BI pipelines beyond raw activity feed.
- Non-tenant global audit (e.g., platform-level infra events) unless emitted via existing services.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Taxonomy/registry and storage model chosen; stream optional via Redis. |
| Implementation | ✅ | Repo/DI/API/stream wired; emitters cover auth, conversations (created/cleared), workflows, billing, storage, vector, containers. |
| Tests & QA | ✅ | Registry/service + repo pagination + API/SSE smoke + emitter hooks covered. |
| Docs & runbooks | ✅ | Activity-log doc + tracker updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- New domain module `app/domain/activity.py` defining `ActivityEvent`, `ActivityEventRepository` protocol, and event action enum/namespaces (e.g., `auth.login.success`, `workflow.run.started`).
- Registry `services/activity/registry.py` enforces allowed actions + metadata schema; validation occurs before persistence.
- Service `ActivityService` providing `record()` plus typed helpers; DI container supplies Postgres repo and no-op fallback for tests.
- Storage: `activity_events` table (JSONB metadata, hashed IP, request_id, actor/object fields) with tenant + action + object indexes; optional partitions.
- API router `api/v1/activity` with list endpoint (filters: time window, action, actor_id, object_type/id, request_id, status) and SSE stream backed by Redis pub/sub (reuse billing backend pattern).
- PII controls: hash IP (reuse existing hash helper), strip secrets from metadata, cap payload sizes.
- Observability: Prometheus counters/gauges for write success/failure and stream lag; structured logs include `activity_event_id`.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Domain & Storage

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Domain | Add `domain/activity.py` with models, enums, repository protocol, validation errors. | Platform Foundations | ✅ |
| A2 | Registry | Implement `services/activity/registry.py` with action taxonomy + metadata schema validation. | Platform Foundations | ✅ |
| A3 | Persistence | Create `infrastructure/persistence/activity/` models + repository; add Alembic migration for `activity_events` with indexes. | Platform Foundations | ✅ |

### Workstream B – Service Layer & DI

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Service | Implement `ActivityService` with typed helper methods and PII scrubbing. | Platform Foundations | ✅ |
| B2 | DI wiring | Register service/repo in `bootstrap/container.py`; provide no-op fallback for tests. | Platform Foundations | ✅ |
| B3 | Metrics | Add Prometheus counters/gauges for write attempts/failures and stream metrics. | Platform Foundations | ✅ |

### Workstream C – API & Streaming

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | REST | Add `api/v1/activity/router.py` with list endpoint, filters, cursor pagination, RBAC scope `activity:read`. | Platform Foundations | ✅ |
| C2 | SSE | Optional: add `GET /activity/stream` reusing billing SSE backend (Redis transport). | Platform Foundations | ✅ |
| C3 | Schemas | Define request/response Pydantic schemas with size limits and stable ordering. | Platform Foundations | ✅ |

### Workstream D – Instrumentation (callers)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Auth | Emit events for signup, login/logout/refresh, password change/reset, email verification, lock/unlock, service-account issuance/revocation. | Platform Foundations | ✅ |
| D2 | Conversations/Agents | Emit conversation created/cleared and run started/ended (per-message logging intentionally skipped). | Platform Foundations | ✅ |
| D3 | Workflows | Emit workflow run start/end; step-level optional follow-up. | Platform Foundations | ✅ |
| D4 | Billing bridge | Bridge normalized billing events into activity feed (state changes only). | Platform Foundations | ✅ |
| D5 | Storage/Vector/Containers | Emit file upload/delete, vector sync state changes, container create/destroy/bind. | Platform Foundations | ✅ |

### Workstream E – Ops, Retention, Docs & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Retention | Add settings + cleanup job/script mirroring run-event cleanup; document defaults. | Platform Foundations | ✅ |
| E2 | Security/RBAC | Define `activity:read` scope, tenant-role defaults (admins), and API guard tests. | Platform Foundations | ✅ |
| E3 | Tests | Unit tests for registry, repo, service; contract tests for API; smoke for SSE. | Platform Foundations | ✅ |
| E4 | Docs | Author `docs/backend/activity-log.md`; update `SNAPSHOT.md` + tracker. | Platform Foundations | ✅ |
| E5 | Validation | Ensure `hatch run lint`, `hatch run typecheck`, and targeted `pytest` suites pass. | Platform Foundations | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design Finalization | Taxonomy, schema, retention defaults, RBAC decisions. | Design reviewed; action enum frozen; doc draft ready. | ✅ | 2025-12-03 |
| P1 – Foundations | Domain/registry/service, Postgres repo + migration, DI wiring, metrics. | Implemented + wired; lint/typecheck green; migration pending apply in envs. | ✅ | 2025-12-10 |
| P2 – API & Streaming | REST list + filters; optional SSE; auth scope; schemas. | Endpoints live; SSE enabled when `ENABLE_ACTIVITY_STREAM=true`. | ✅ | 2025-12-14 |
| P3 – Instrumentation | Auth, conversations/agents, workflows, billing bridge, storage/vector/container emitters. | Conversation created/cleared + workflow/billing/vector/container hooks shipped; no per-message logging by design. | ✅ | 2025-12-18 |
| P4 – Hardening & Ops | Retention job, PII scrubbing, load/perf sanity, docs, tracker update. | Cleanup script + settings + doc done; repo/API/SSE/emitter tests green; tracker updated. | ✅ | 2025-12-22 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Postgres migration window (alembic via `just migration-revision` / `just migrate`).
- Redis available for SSE transport (reuse billing transport). If unavailable, stream endpoint ships disabled.
- Auth scope addition in tokens (`activity:read`) and frontend proxy once UI consumers exist.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Event volume balloons (chat runs) | High storage + query cost | Indexes + partitioning option; retention defaults; avoid dumping full payloads. |
| PII leakage via metadata | Compliance risk | Strict schema + scrub/whitelist; hash IPs; size limits; review instrumentation PRs. |
| RBAC gaps expose tenant data | Security | New scope + tenant checks; contract tests for cross-tenant isolation. |
| Migration slip blocks deploy | Schedule | Run migration early; keep repo DI no-op for tests; guard writes if table missing (feature flag). |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Commands: `hatch run lint`, `hatch run typecheck`, `pytest apps/api-service/tests/unit/activity apps/api-service/tests/contract/test_activity_api.py`, targeted smoke hitting `/api/v1/activity` (and `/activity/stream` if enabled).
- Verify migration applies and rolls back cleanly against local Postgres (`just migrate`).
- Manual sanity: trigger login, conversation message, workflow run; confirm activity rows and filtered queries return expected entries; check metrics and logs include event IDs.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Deploy migration first; service is backward-compatible (no-op repo if table absent, but writes best-effort).
- Configure retention (`Settings.retention.activity_days`) and Redis URL for SSE; default SSE off if Redis missing.
- No feature flags; access controlled via scope + tenant role. Add backfill script later if needed.
- Alembic heads merged into `20251202_120000`; apply this revision to align environments before further deploys.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-01 — Initial milestone drafted (planning status).
- 2025-12-01 — Foundations, API, migration, initial emitters, and docs landed; milestone now In Progress.
- 2025-12-01 — Instrumentation finished (conversation.created, billing/vector/container hooks), repo/API/SSE/emitter tests added, tracker/doc refreshed; milestone marked complete.
- 2025-12-02 — Alembic heads merged to `20251202_120000`; rollout note updated and resume-ready remediation recorded.
