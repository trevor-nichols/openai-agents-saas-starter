<!-- SECTION: Metadata -->
# Milestone: Workflow Run Deletion

_Last updated: 2025-12-01_  
**Status:** Implemented (tests pending)  
**Owner:** @codex  
**Domain:** Backend | Frontend  
**ID / Links:** BE-013, FE-110 (ISSUE_TRACKER.md)

---

## Objective

Add tenant-scoped deletion for workflow runs (soft delete by default, optional hard purge) with clear auth/role guards, retention guardrails, and UI affordances aligned with chat conversation deletion.

---

## Definition of Done

- FastAPI exposes `DELETE /api/v1/workflows/runs/{run_id}` with scope/role guards.
- Workflow runs/steps gain soft-delete columns; default queries exclude deleted items.
- Hard purge path exists with retention guard (configurable) and audited actor/reason.
- Repository/service/unit/API tests cover soft/hard delete and visibility filtering.
- OpenAPI/SDK regenerated after backend lands; UI adds delete affordance (FE-110).
- `pnpm lint` / `pnpm type-check` (frontend) and `hatch run lint` / `hatch run typecheck` (backend) pass.
- Tracker/docs updated (this file + ISSUE_TRACKER.md entries).

---

## Scope

### In Scope
- DB schema changes for workflow run/step soft-delete metadata.
- Repository/service logic for soft delete and hard purge.
- New FastAPI delete endpoint with role/scope enforcement and retention guard.
- Settings knob for minimum purge age; logging/metrics for delete operations.
- Backend tests (unit + contract/API).

### Out of Scope
- UI deletion UX (tracked separately in FE-110).
- Historical backfill/legacy compatibility (none required).
- Cross-tenant admin/operator superpowers beyond current role model.

---

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan agreed: soft delete default, optional hard purge with guardrail. |
| Implementation | ✅ | Backend + frontend delete flows coded; structured logs/metrics added. |
| Tests & QA | ⚠️ | New tests added; `hatch run lint/typecheck` and `pnpm lint/type-check` still need to be run. |
| Docs & runbooks | ✅ | Tracker + ISSUE_TRACKER updated; logging/metrics scope captured here. |

---

## Architecture / Design Snapshot

- Soft delete fields: `deleted_at`, `deleted_by`, `deleted_reason` on `workflow_runs` + `workflow_run_steps`.
- Default queries exclude deleted rows; optional `include_deleted` flag for internal use.
- New repository methods: `soft_delete_run`, `hard_delete_run`.
- Service method `delete_run` enforces tenant ownership, scopes, retention guard, and hard/soft path.
- API route `DELETE /api/v1/workflows/runs/{run_id}` (scope `workflows:delete`, role ≥ admin).
- Retention knob `WORKFLOW_MIN_PURGE_AGE_HOURS` (default 0) to block hard purge for recent runs unless forced.
- Audit: structured log/metric per delete (soft/hard).

---

## Workstreams & Tasks

### WS1 – Data model & migration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| WS1.1 | DB | Add soft-delete columns via Alembic; update models | @codex | ✅ |
| WS1.2 | Domain | Extend `WorkflowRun`/`WorkflowRunStep` dataclasses | @codex | ✅ |

### WS2 – Repository & service layer

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| WS2.1 | Repo | Implement soft/hard delete, filtering, retention checks | @codex | ✅ |
| WS2.2 | Service | Add `delete_run` with tenant guard + retention guardrail | @codex | ✅ (with structured logs/metrics) |

### WS3 – API surface

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| WS3.1 | FastAPI | Add DELETE route, scope/role guard, 204/404/409 responses | @codex | ✅ |
| WS3.2 | OpenAPI | Regenerate schema/SDK after backend lands | @codex | ✅ (fixtures/spec regenerated) |

### WS4 – Tests & validation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| WS4.1 | Unit | Repo/service tests for soft/hard delete and filtering | @codex | ✅ |
| WS4.2 | Contract/API | FastAPI endpoint tests (204/404/409) | @codex | ✅ |
| WS4.3 | QA | `hatch run lint`, `hatch run typecheck` | @codex | ⚠️ Pending local run |

---

## Dependencies

- None blocking; no backward-compat or data backfill required (pre-release).
- FE-110 depends on BE-013 landing first.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Mis-scoped deletes across tenants | High | Enforce tenant_id in repo queries; 404 on mismatch. |
| Hard purge bypassing retention unintentionally | Medium | Default retention guard; require explicit `hard=true` and scope/role. |
| Missed filtering of deleted runs | Medium | Default filters in repo/list/get; tests verifying exclusion. |

---

## Validation / QA Plan

- Unit: `tests/unit/workflows/test_workflow_run_repository.py` (soft/hard delete, filtering).
- Contract/API: extend `tests/contract/test_workflows_api.py` for DELETE behavior.
- Static: `hatch run lint`, `hatch run typecheck`.
- Regenerate OpenAPI/SDK post-merge (frontend uses generated types).

---

## Rollout / Ops Notes

- Run Alembic migration via `just migrate`.
- No data backfill required; existing rows treated as active (`deleted_at IS NULL`).
- Configure retention via `WORKFLOW_MIN_PURGE_AGE_HOURS` as needed.

---

## Changelog

- 2025-12-01 — Added soft/hard delete implementation, structured logs + metrics, SDK regen, and frontend delete affordance.  
- 2025-12-01 — Created milestone doc and implementation plan (BE-013 / FE-110).  
