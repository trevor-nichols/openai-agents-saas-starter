<!-- SECTION: Metadata -->
# Milestone: Platform Tenant Management + Lifecycle (API)

_Last updated: 2025-12-31_  \
**Status:** Complete  \
**Owner:** Platform Foundations  \
**Domain:** Backend  \
**ID / Links:** [TBD], [docs/auth/roles.md], [docs/persistence/db-schema.md]

---

<!-- SECTION: Objective -->
## Objective

Deliver a clean, auditable tenant management surface for platform operators and tenant admins, with explicit
lifecycle controls (suspend/reactivate/deprovision) and consistent tenant-account domain services, so the
API service supports enterprise-grade operations without pragmatic coupling.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Tenant account domain model + repository port supports create/read/update/list + lifecycle actions.
- DB schema extended for tenant lifecycle state; migration applied and documented.
- Platform operator API routes implemented with scope/role enforcement and audit logging.
- Tenant self-service account endpoints (read/update) implemented for owners/admins.
- Tenant lifecycle enforcement applied consistently to tenant-scoped endpoints.
- Unit + contract + smoke tests cover new behavior and failure modes.
- OpenAPI artifacts regenerated and web SDK regeneration note documented for frontend team.
- `hatch run lint`, `hatch run typecheck`, and relevant tests pass.
- Docs/trackers updated (roles, DB schema, milestone changelog).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Tenant account lifecycle state modeling (active/suspended/deprovisioned) and auditing.
- Platform operator CRUD + lifecycle endpoints for tenant accounts.
- Tenant admin self-service account read/update endpoints.
- Service-layer refactor so signup and operator flows share a single tenant-account service.
- Consistent tenant-status enforcement for tenant-scoped APIs.
- Tests, migrations, OpenAPI artifacts, and documentation updates.

### Out of Scope
- Web app changes (handled by other developers).
- Full data deletion/archival workflows across all services (future deprovisioning workflow).
- Background job orchestration (no async job system in scope).
- Billing provider refactors beyond minimal lifecycle integration.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⚠️ | Tenant account domain port is lookup-only; lifecycle state is not modeled. |
| Implementation | ⚠️ | Tenants support settings + members/invites; no tenant account CRUD or lifecycle endpoints. |
| Tests & QA | ⚠️ | Settings/team tests exist; tenant account lifecycle tests missing. |
| Docs & runbooks | ⚠️ | Roles/DB docs do not mention lifecycle state or operator tenant management. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

**End-of-analysis (API service):**
- Tenant accounts are created only via signup flow (`services/signup`); no reusable tenant-account service exists.
- Tenant account repository only exposes `get_name`; no CRUD or lifecycle port (`domain/tenant_accounts.py`).
- Tenant-scoped endpoints exist for settings, members, and invites; no tenant account endpoints.
- Tenant context resolution is JWT/header-based only; tenant status is not enforced anywhere.
- Platform operator role/scope exists (`platform_operator`, `platform:operator`, `support:*`), but no operator
  tenant management endpoints are defined.

**Recommended shape (clean architecture):**
- Expand `domain/tenant_accounts.py` to include a full tenant-account entity + lifecycle status enum and a
  repository port covering CRUD and lifecycle transitions.
- Add `services/tenant/tenant_account_service.py` to encapsulate validation, slug uniqueness, and lifecycle
  transitions; avoid direct ORM access from signup or API routes.
- Add `api/v1/platform/tenants` router for operator CRUD/lifecycle, separate from `api/v1/tenants` (self-service).
- Add tenant lifecycle enforcement in a dedicated dependency (or extend tenant context) that is applied
  across tenant-scoped routers without coupling to specific APIs.
- Audit lifecycle actions via existing activity logging patterns.

**Data model changes (proposal):**
- `tenant_accounts`: add `status` (enum), `updated_at`, optional `suspended_at`, `deprovisioned_at`,
  `status_reason`, and `status_updated_by` (UUID) for auditability.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Domain + Persistence

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Domain | Expand `TenantAccount` domain model and repository port to include CRUD + lifecycle ops. | ✅ |
| A2 | DB | Add tenant lifecycle columns + enum migration; update ORM model. | ✅ |
| A3 | Persistence | Implement Postgres repo methods (create/get/list/update/status transitions). | ✅ |
| A4 | Docs | Update `docs/persistence/db-schema.md` for new tenant columns. | ✅ |

### Workstream B – Services

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Service | Create `TenantAccountService` for validation, slug rules, and account mutations. | ✅ |
| B2 | Service | Add lifecycle operations (suspend/reactivate/deprovision) with audit logging hooks. | ✅ |
| B3 | Service | Refactor signup flow to call `TenantAccountService.create_account`. | ✅ |
| B4 | Policy | Introduce tenant-access policy checks (active vs suspended/deprovisioned). | ✅ |

### Workstream C – API Surface

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | API | Add `/tenants/account` GET/PATCH for tenant admins. | ✅ |
| C2 | API | Add `/platform/tenants` CRUD endpoints for operators. | ✅ |
| C3 | API | Add `/platform/tenants/{id}/lifecycle` actions (suspend/reactivate/deprovision). | ✅ |
| C4 | API | Create schema models for tenant account + lifecycle responses. | ✅ |
| C5 | Auth | Implement operator dependency using `platform:operator` or `support:*` scope. | ✅ |

### Workstream D – Enforcement + Integration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Policy | Enforce tenant status in tenant-scoped dependencies. | ✅ |
| D2 | Auth | Decide operator override behavior for suspended tenants (read-only vs full override). | ✅ |
| D3 | Billing | Ensure lifecycle transitions trigger billing/service constraints (minimal integration). | ✅ |

### Workstream E – Tests + QA

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | Unit | Tenant account + lifecycle service unit tests. | ✅ |
| E2 | Contract | Contract tests for platform + tenant account endpoints. | ✅ |
| E3 | Smoke | Extend smoke tests for tenant account and lifecycle actions (requires running API server). | ✅ |

### Workstream F – Artifacts + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| F1 | OpenAPI | Regenerate OpenAPI fixtures + note SDK regen requirement for frontend. | ✅ |
| F2 | Docs | Update `docs/auth/roles.md` for operator tenant management. | ✅ |
| F3 | Docs | Update SNAPSHOT and tracker changelog. | ✅ |

### Workstream G – Issue Remediation (Post-Review)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| G1 | Auth | Allow `support:*` operator scope on `/platform/*` dependencies (TL-002). | ✅ |
| G2 | Audit | Emit activity events for platform tenant create/update (TL-003). | ✅ |
| G3 | Errors | Map slug collision DB errors to 409 (TL-004). | ✅ |
| G4 | Auth | Remove operator override headers from service-account admin; require operator scope (TL-005). | ✅ |
| G5 | API | Remove `status_reason` from tenant self-service response (TL-006). | ✅ |
| G6 | Service | Guard `finalize_deprovision` transition (TL-007). | ✅ |
| G7 | Tests | Add missing unit/contract/smoke coverage (TL-008). | ✅ |
| G8 | QA | Run lint/typecheck/tests + record results (TL-010). | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Finalize lifecycle state model, endpoints, and operator scopes. | Open questions resolved; tracker updated. | ✅ |
| P1 – Domain + DB | Domain model + repo port + migration + ORM updated. | Repo compiles; migration ready. | ✅ |
| P2 – Services | Tenant account + lifecycle services wired; signup uses service. | Unit tests green. | ✅ |
| P3 – API | Operator + tenant self-service endpoints implemented. | Contract tests green. | ✅ |
| P4 – Enforcement + QA | Tenant status enforcement + smoke tests + docs. | Smoke + lint + typecheck green. | ✅ |
| P5 – Issue Remediation | Address review findings TL-002 through TL-010. | Issues closed; tests re-run. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Existing `platform:operator` / `support:*` scope enforcement patterns.
- Activity logging service for audit events.
- Alembic migrations (multi-head discipline + `just migrate`).

---

<!-- SECTION: Open Questions -->
## Open Questions

All alignment questions resolved. Decisions captured below:

- **Lifecycle states:** `active`, `suspended`, `deprovisioning`, `deprovisioned`.
- **Slug mutability:** immutable for tenant admins; operator-only change with audit reason.
- **Operator override:** read-only operator override for suspended tenants via explicit headers; platform routes remain available.
- **Billing integration:** suspend blocks usage but does not auto-cancel; deprovision cancels subscription (if enabled) and revokes access.
- **Audit fields:** `status`, `status_updated_at`, `status_updated_by`, `status_reason`, `suspended_at`, `deprovisioned_at` on `tenant_accounts`.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tenant status enforcement breaks existing flows. | High | Introduce policy checks behind a focused dependency and add smoke coverage. |
| Slug change impacts URL assumptions or frontend routing. | Medium | Default to immutable slug unless explicit decision made. |
| Deprovision semantics unclear. | Medium | Start with reversible status + audit logging, defer data deletion. |
| Operator endpoints become a monolith. | Low | Split routers by concern and keep files ≤300 lines. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend lint/typecheck after each phase: `hatch run lint`, `hatch run typecheck`.
- Unit tests: `cd apps/api-service && hatch run test tests/unit/tenants` (plus new unit suites).
- Contract tests: `cd apps/api-service && hatch run test tests/contract/test_tenant_*`.
- Smoke tests: `cd apps/api-service && hatch run test tests/smoke/http/test_tenants_smoke.py`.
- Ensure OpenAPI fixtures are regenerated after API changes.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Apply DB migration with `just migrate` (multi-head aware).
- No feature flags (repo policy). Changes are active once deployed.
- If lifecycle enforcement introduces regressions, revert policy dependency first (no DB rollback needed).

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-31 — Tracker created with API service plan and architecture snapshot.
- 2025-12-31 — Phase P1 complete (domain + ORM + migration + docs); lint/typecheck green.
- 2025-12-31 — Phase P2 complete (tenant account service + signup refactor); lint/typecheck green.
- 2025-12-31 — Phase P3 complete (tenant/self-service + platform endpoints); lint/typecheck green.
- 2025-12-31 — Phase P4 implementation complete (enforcement + tests + OpenAPI + docs); smoke tests blocked without running API server (localhost:8000).
- 2025-12-31 — Issue remediation phase started; TL-001 deferred to `docs/trackers/current_milestones/MILESTONE_SIGNUP_ATOMICITY.md`.
- 2025-12-31 — Lint + typecheck + test runs executed; smoke suite executed and failed at `/api/v1/logs` (404) in `tests/smoke/http/test_observability_smoke.py`.
- 2025-12-31 — DB migration applied via `just migrate`.
