<!-- SECTION: Metadata -->
# Milestone: Split Fixture SDK + GCS Typing Fix

_Last updated: 2026-01-04_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** PR #81, CI failures (frontend-quality, backend-quality, build-web)

---

<!-- SECTION: Objective -->
## Objective

Deliver a clean, maintainable split between production and fixture-only OpenAPI SDKs for the web app, and remove Pyright/Mypy noise in the GCS storage provider by adopting a type-checker-friendly import pattern.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Web app uses a fixture-only SDK generated from `openapi-fixtures.json` with a dedicated output path.
- Server-only fixture service imports fixture types/functions from the fixture SDK (no cross-coupling with production SDK).
- OpenAPI generation/docs describe both SDKs clearly.
- GCS provider import no longer requires `type: ignore`, and Pyright/Mypy pass.
- Frontend: `pnpm lint` + `pnpm type-check` pass.
- Backend: `hatch run lint` + `hatch run typecheck` pass.
- Tracker phases signed off with validation results.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add a fixture-only OpenAPI SDK config and output directory for the web app.
- Update server-side fixture service to use the fixture SDK and a dedicated client factory.
- Update docs/scripts to reflect the split SDK generation.
- Fix GCS storage provider import to satisfy static typing.

### Out of Scope
- Changes to backend API schema or fixture endpoints.
- New fixture capabilities or auth changes.
- Production runtime behavior changes beyond typing/tooling.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Clear boundary between prod vs fixture SDKs selected. |
| Implementation | ✅ | Frontend split + backend typing fix complete. |
| Tests & QA | ✅ | Frontend + backend checks green. |
| Docs & runbooks | ✅ | Updated data-access + web app OpenAPI guidance. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce a dedicated fixture SDK output under `apps/web-app/lib/api/fixtures-client` generated from `apps/api-service/.artifacts/openapi-fixtures.json`.
- Keep the production SDK untouched at `apps/web-app/lib/api/client` (generated from `openapi.json`).
- Server-only fixture services use a dedicated fixtures API client factory to avoid coupling with the production client.
- GCS provider switches to `import google.cloud.storage as storage` to avoid namespace-package `attr-defined` issues in type checkers while keeping official client usage.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Frontend SDK Split

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Tooling | Add fixtures OpenAPI config + generation script | ✅ |
| A2 | Web app | Add fixtures API client factory | ✅ |
| A3 | Web app | Update fixture service imports to fixtures SDK | ✅ |
| A4 | Docs | Update web app OpenAPI generation docs | ✅ |

### Workstream B – Backend Typing Fix

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Storage | Update GCS import to typed module import | ✅ |
| B2 | QA | Run backend lint/typecheck | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Confirm approach + tracker created | Tracker approved by owner | ✅ |
| P1 – Frontend fixtures SDK | Implement Workstream A; run `pnpm lint` + `pnpm type-check` | Frontend checks green | ✅ |
| P2 – Backend typing fix | Implement Workstream B; run `hatch run lint` + `hatch run typecheck` | Backend checks green | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Existing OpenAPI artifacts in `apps/api-service/.artifacts/`.
- `@hey-api/openapi-ts` tooling and `openapi-ts` CLI.
- `google-cloud-storage` library installed in backend env.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Fixture SDK drift from prod SDK config | Medium | Duplicate config fields intentionally; document both paths. |
| Additional maintenance for two SDK outputs | Low | Scripted generation and documented workflow. |
| Type checker regressions in GCS provider | Low | Use module import recognized by Pyright/Mypy. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Frontend: `cd apps/web-app && pnpm lint && pnpm type-check`.
- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck`.
- (Optional) `pnpm --filter web-app build` to confirm Docker build stage readiness.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No runtime migration. Tooling-only updates.
- Generated SDK artifacts should be committed after regeneration.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-04 — Tracker created and approach confirmed.
- 2026-01-04 — Phase P1 complete; fixture SDK split implemented; `pnpm lint` + `pnpm type-check` green.
- 2026-01-04 — Phase P2 complete; GCS typing fix + mypy override; `hatch run lint` + `hatch run typecheck` green.
- 2026-01-04 — Replaced `use server` with `server-only` in `lib/server` utilities; `pnpm --filter web-app build` succeeded (feature-flag fetch warnings during prerender).
