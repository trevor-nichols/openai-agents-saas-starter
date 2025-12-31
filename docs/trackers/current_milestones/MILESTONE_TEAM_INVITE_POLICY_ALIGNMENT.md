<!-- SECTION: Metadata -->
# Milestone: Team Invite Policy Alignment

_Last updated: 2025-12-30_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** [docs/auth/roles.md]

---

<!-- SECTION: Objective -->
## Objective

Align team invite policy across backend and frontend with a single source of truth, expose it via a stable API, and close remaining edge-case gaps (validation + race handling) to keep team management production-grade.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Invite expiry policy is defined once in backend constants and reused in API schema + service logic.
- New `/api/v1/tenants/invites/policy` endpoint returns default + max expiry hours.
- Frontend consumes policy and enforces consistent validation/limits.
- Invite acceptance validates `display_name` length at API boundary.
- Membership add handles unique-constraint races and returns a conflict error.
- Tests and docs updated as needed.
- `hatch run lint` / `hatch run typecheck` / `pnpm lint` / `pnpm type-check` are green.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend policy constants + shared usage.
- Team invite policy endpoint.
- Frontend policy consumption + UI validation alignment.
- Membership add race handling.
- API validation for invite acceptance display name.

### Out of Scope
- Any new invite types or notification providers.
- Backward compatibility shims.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Policy centralized + explicit API contract shipped. |
| Implementation | ✅ | Backend + frontend wired to shared policy. |
| Tests & QA | ✅ | Backend + frontend lint/typecheck run. |
| Docs & runbooks | ✅ | Tracker + coverage matrix updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce backend policy constants for invite expiry (default + max) under the team domain.
- Wire policy into API schema and service logic to eliminate drift.
- Add a small policy endpoint under tenant invite routes to allow UI to hydrate limits.
- Frontend fetches policy via BFF and uses it for form validation / max values.
- Membership add handles integrity errors to avoid 500s under concurrent writes.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Backend Policy + API

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Domain | Add invite policy constants + use in service | ✅ |
| A2 | API | Add policy endpoint + reuse constants in schemas | ✅ |
| A3 | Validation | Add display_name max length in accept request | ✅ |
| A4 | Persistence | Handle membership unique constraint race | ✅ |

### Workstream B – Frontend Alignment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Server | Add server service to fetch invite policy | ✅ |
| B2 | UI | Use policy in invite form validation + input limits | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Policy drift between backend and frontend | Med | Single source of truth + policy endpoint. |
| Additional endpoint adds surface area | Low | Keep endpoint minimal/read-only. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck`
- Frontend: `cd apps/web-app && pnpm lint && pnpm type-check`
- Optional: run relevant unit tests (team invite + membership).

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations required.
- New endpoint is read-only and safe to deploy immediately.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-30 — Tracker created for team invite policy alignment and professionalization.
- 2025-12-30 — Policy constants + endpoint shipped; frontend aligned; tests updated.
