<!-- SECTION: Metadata -->
# Milestone: Tenant Role Enum Propagation

_Last updated: 2025-12-30_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** Related tracker: docs/trackers/complete/2025-12-29/MILESTONE_TEAM_ORG_MANAGEMENT.md

---

<!-- SECTION: Objective -->
## Objective

Make tenant roles a single source of truth across domain, API, OpenAPI, SDK, and frontend by propagating the TenantRole enum end-to-end and enforcing database integrity.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- TenantRole replaces role strings in domain models and service contracts.
- API request/response schemas use TenantRole (OpenAPI enum is emitted).
- Database enforces allowed role values (check constraints or enum type).
- OpenAPI artifacts and web SDK are regenerated from the new schema.
- Frontend uses generated SDK types for role values (no hand-maintained unions).
- Tests updated and passing for backend and frontend.
- Docs/trackers updated.
- `hatch run lint` and `hatch run typecheck` pass for the backend.
- `pnpm lint` and `pnpm type-check` pass for the web app.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Promote TenantRole into domain models (team + user membership) and service interfaces.
- Update API schemas to use TenantRole for team membership and invites.
- Update persistence layer conversions and add database constraints on role columns.
- Regenerate OpenAPI + SDK artifacts and update frontend usage to rely on generated enums.
- Align tests with enum usage and update fixtures if needed.

### Out of Scope
- Redesigning authorization or permission models.
- Introducing new role types beyond the existing four.
- Backward compatibility layers for legacy role strings.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | OK | Clear single-source-of-truth plan via TenantRole. |
| Implementation | OK | Backend + frontend enum propagation complete; migration + SDK regen done. |
| Tests & QA | OK | Backend + web-app test suites green. |
| Docs & runbooks | OK | Tracker updated; no additional doc changes required. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Canonical enum stays in `apps/api-service/src/app/domain/tenant_roles.py`.
- TenantRole is used end-to-end (domain models, API schemas, authenticated user payloads).
- Persistence uses SQLAlchemy Enum for tenant-role columns to enforce values and align with existing enum usage.
- `platform_operator` remains a separate platform-level role, stored on the user record (not part of TenantRole).
- JWT `roles` claim is authoritative for tenant role; scopes are only used to infer a tenant role when no `roles` claim exists.
- DB uses Postgres enums (`tenant_role`, `platform_role`) without cross-field constraints until an internal-operator flag exists.
- OpenAPI schema emits the enum; TS SDK types are generated and used by the UI.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A - Domain + Persistence

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Domain | Replace role: str with TenantRole in domain DTOs/models (team + users). | done |
| A2 | Persistence | Convert DB reads/writes to/from TenantRole and update repositories. | done |
| A3 | DB | Add tenant role enum constraints via Alembic migration. | done |

### Workstream B - API + Auth

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | API schemas | Use TenantRole in team API request/response models. | done |
| B2 | Services | Update service interfaces and validations to accept TenantRole. | done |

### Workstream C - OpenAPI + Frontend

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | OpenAPI | Export OpenAPI fixtures and regenerate web SDK. | done |
| C2 | Frontend | Replace manual role unions with generated types; update UI mappings. | done |

### Workstream D - Tests + Docs

| ID | Area | Description | Status |
|----|------|-------------|--------|
| D1 | Tests | Update unit/contract/smoke tests to use enum values. | done |
| D2 | Docs | Update role references in docs if needed. | done |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 - Alignment | Confirm role taxonomy + DB constraint choice | Design signed off | done |
| P1 - Backend | Domain + API + DB changes | Backend builds, tests green | done |
| P2 - Frontend | SDK regen + UI updates | Frontend builds, tests green | done |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None beyond standard OpenAPI/SDK regeneration flow.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| DB constraint blocks invalid legacy data | Low | No public data; validate before migration if needed. |
| Type changes ripple to SDK/tests | Medium | Regenerate OpenAPI + SDK early; update tests in same PR. |
| Enum mismatch between backend and frontend | Medium | Use generated SDK types exclusively. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `hatch run lint`, `hatch run typecheck`, and relevant unit/contract/smoke tests.
- Frontend: `pnpm lint`, `pnpm type-check`, and affected Playwright/Vitest tests.
- Verify OpenAPI export + SDK generation completes successfully.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Run DB migration via `just migrate`.
- Regenerate OpenAPI + SDK before touching web-app code.
- No backward compatibility required; rollback via migration revert if needed.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-30 - Created milestone tracker for TenantRole enum propagation.
- 2025-12-30 - Alignment: TenantRole canonical, PlatformRole separate; roles claim authoritative; backend/frontend implementation in progress.
- 2025-12-30 - Lint/typecheck completed for backend + web-app; suite runs pending.
- 2025-12-30 - Backend + web-app tests green; milestone complete.
