<!-- SECTION: Metadata -->
# Frontend Test Architecture v2 (Harness + Fixtures)

_Last updated: 2025-12-30_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** apps/web-app/tests/README.md, apps/web-app/tests/harness/*, apps/web-app/tests/fixtures/*, apps/web-app/playwright.config.ts, apps/web-app/vitest.config.mts, apps/api-service/src/app/services/service_account_bridge.py

---

<!-- SECTION: Objective -->
## Objective

Deliver a professional, deterministic frontend test architecture with a formal harness, typed env contract, and Playwright fixtures while aligning backend test dependencies (fixtures + Vault behavior) so E2E runs are repeatable and audit-ready.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `apps/web-app/tests/harness/` provides the canonical env + fixtures + seeding contract (typed, validated, documented).
- Playwright specs rely on fixtures instead of ad‑hoc helpers; auth/storage state handled centrally.
- Global setup is deterministic and fails fast when fixtures/env are invalid.
- Backend alignment: Vault fallback is gated to fixtures/dev, and billing test gateway remains deterministic.
- Generated artifacts are ignored and documented (`tests/.fixtures.json`, `.env.local.playwright`, `.playwright-downloads/`).
- `apps/web-app/tests/README.md` is the single source of truth for test architecture.
- `pnpm lint`, `pnpm type-check`, `pnpm test`, and `pnpm test:e2e` pass in intended environments.
- Tracker updated with decisions + validation notes.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Formal Playwright test harness (env validation, fixture schema, seed orchestration).
- Playwright fixtures for tenant-admin/operator roles and API helpers.
- Refactor existing E2E specs to use fixtures/harness.
- Update test docs + placement rules + generated artifact ignores.
- Backend alignment required for deterministic E2E (Vault signing fallback gating, fixture billing gateway wiring).

### Out of Scope
- Expanding coverage or rewriting all existing tests beyond architectural refactor.
- Cross-browser E2E beyond existing Chromium projects.
- Performance/load testing, visual regression tooling.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Harness + fixtures finalized with clear module boundaries. |
| Implementation | ✅ | Harness, fixtures, and refactor landed. |
| Tests & QA | ⏳ | Architecture updated; validation commands still need to be run. |
| Docs & runbooks | ✅ | README + snapshots updated for new harness. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Harness-first:** `tests/harness/` owns env schema, fixture schema, and seed orchestration.
- **Typed env contract:** Zod-validated Playwright env with derived booleans and defaults aligned to `seeds/playwright.yaml`.
- **Playwright fixtures:** `tests/fixtures/` provides role-based pages and API helpers; specs no longer manage storage state directly.
- **Deterministic seeding:** `pnpm test:seed` remains the canonical seeding entrypoint; harness validates `.fixtures.json` shape.
- **Backend alignment:** Vault fallback signatures are allowed only when `USE_TEST_FIXTURES=true`; billing gateway uses fixture implementation in test mode.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Milestone & Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Docs | Rewrite milestone tracker with final architecture decisions | ✅ |
| A2 | Docs | Update `apps/web-app/tests/README.md` for harness + fixtures | ✅ |
| A3 | Docs | Update placement rules + ignore list | ✅ |

### Workstream B – Harness + Env Contract

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Infra | Add `tests/harness/env.ts` (Zod schema + derived flags) | ✅ |
| B2 | Infra | Add fixture schema + reader (`tests/harness/fixtures.ts`) | ✅ |
| B3 | Infra | Add seed orchestration helpers (`tests/harness/seed.ts`) | ✅ |
| B4 | Infra | Centralize storage-state paths + freshness logic | ✅ |

### Workstream C – Playwright Fixtures + Spec Refactor

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | E2E | Create fixtures for tenant admin/operator roles | ✅ |
| C2 | E2E | Refactor specs to use fixtures/harness | ✅ |
| C3 | E2E | Simplify global setup and remove ad‑hoc env helpers | ✅ |

### Workstream D – Backend Alignment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | API | Gate Vault fallback signing behind `USE_TEST_FIXTURES` | ✅ |
| D2 | API | Validate fixture billing gateway wiring for tests | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Backend `/api/v1/test-fixtures/*` endpoints enabled via `USE_TEST_FIXTURES=true`.
- Starter Console seed workflows available for deterministic data.
- Local infra (Redis/Vault) for provider-dependent flows.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Env drift between docs and harness | Medium | Single Zod contract used by Playwright + docs. |
| Fixture schema changes without validation | Medium | Validate `.fixtures.json` on read and fail fast. |
| Vault fallback in non-test env | High | Gate fallback to `USE_TEST_FIXTURES` only. |
| Longer local setup time | Medium | Global setup caches storage state + optional seed flags. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `pnpm lint`
- `pnpm type-check`
- `pnpm test`
- `pnpm test:e2e` (requires seeded fixtures + real backend)

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No production rollout changes.
- New harness requires `PLAYWRIGHT_*` env vars documented in `apps/web-app/tests/README.md`.
- Vault fallback signing only allowed when `USE_TEST_FIXTURES=true`.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-30 — Rewrote milestone with harness/fixtures architecture and backend alignment.
- 2025-12-30 — Implemented harness + fixtures, refactored Playwright specs, and gated Vault fallback for tests.
