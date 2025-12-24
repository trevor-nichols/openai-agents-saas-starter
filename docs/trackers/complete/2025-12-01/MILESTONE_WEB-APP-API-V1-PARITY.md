<!-- SECTION: Metadata -->
# Milestone: Web App API v1 Parity

_Last updated: 2025-12-01_  
**Status:** Planned  
**Owner:** @platform-foundations  
**Domain:** Frontend  
**ID / Links:** [docs/architecture/fast-api-endpoints.md], [apps/web-app/SNAPSHOT.md]

---

<!-- SECTION: Objective -->
## Objective

Align all Next.js route handlers under `apps/web-app/app/api` to mirror the FastAPI `/api/v1` surface: same paths, verbs, and response semantics. Eliminate unversioned/alias routes so browser clients and SDK consumers use a single, predictable BFF contract consistent with the backend documentation.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- All route handlers live under `/api/v1/...` and map 1:1 to endpoints listed in `docs/architecture/fast-api-endpoints.md` (paths + HTTP methods).
- Old unversioned or alias routes are removed or explicitly redirected with tests updated accordingly.
- Missing backend endpoints (e.g., `/health/storage`, `/api/v1/auth/token`, Stripe webhook, status subscription paths) have BFF parity or are documented as intentionally omitted.
- Client callsites (hooks, services, components) use the new paths; helper utilities expose a single base path to avoid future drift.
- Route handler + affected unit tests pass; pnpm lint + pnpm type-check are green for `apps/web-app`.
- SNAPSHOT/docs/trackers updated to reflect the new API structure.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Restructuring Next.js API route folders to `/api/v1/...` for all documented endpoints.
- Reconciling mismatches and gaps (e.g., health storage check, billing/event paths, container bind path suffix).
- Updating web-app fetchers/query hooks/components to call the new BFF routes.
- Updating/adding route handler tests and any affected integration/unit tests.
- Documentation updates: SNAPSHOT adjustments (app/api tree), data-access notes if path helpers change.

### Out of Scope
- Changes to FastAPI backend behavior or contract itself.
- Introducing new product features beyond parity (e.g., new resources not in backend spec).
- Reworking authentication/session model beyond required path adjustments.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | V1 namespace adopted; legacy aliases limited to status-subscriptions redirect + root health copies. |
| Implementation | ✅ | All handlers rehomed under `/api/v1`; container bind, workflow run-stream, vector-store create merged; status webhook paths added. |
| Tests & QA | ⚠️ | New coverage added for auth/token, status verify/challenge/delete, health/storage; still need broader regression smoke. |
| Docs & runbooks | ⏳ | Milestone updated; SNAPSHOT/docs pending refresh. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Adopt a single BFF namespace: `app/api/v1/<resource>` mirroring FastAPI paths; remove top-level unversioned duplicates.
- Introduce a shared path helper (e.g., `lib/server/apiPaths.ts`) to prevent future drift and simplify refactors.
- Decide per-endpoint handling:
  - Health: add `/health/storage`; evaluate `/health/features` (either move under `/v1/health/features` or drop if unused).
  - Default: assess need for `/` and `/webhooks/stripe` BFF proxies (likely pass-through or intentional omission with doc note).
  - Status subscriptions: consolidate `status-subscriptions` aliases into `/v1/status/subscriptions` routes.
  - Containers: ensure bind/unbind routes match `/api/v1/containers/agents/{agent_key}/container` suffix.
  - Vector stores: collapse `/create` helper into RESTful POST on base resource.
- Keep data layer abstraction: route handlers continue to call generated SDK via `getServerApiClient`, but path/version drift is solved at the Next.js routing layer.

### Mapping Snapshot (A1 draft)

| Backend path (method) | Current Next path | Gap / action |
| --- | --- | --- |
| `/health`, `/health/ready`, `/health/storage` (GET) | `/health`, `/health/ready`, `/health/features` | Add storage; decide fate of `features`; consider keeping health unversioned to match backend or mirror under `/v1/health`. |
| `/` (GET), `/webhooks/stripe` (POST) | none | Likely no BFF proxy; document as intentionally omitted. |
| `/api/v1/auth/token` (POST) | none | Add login proxy. |
| `/api/v1/auth/refresh` (POST) | `/auth/refresh` | Move to `/v1/auth/refresh`. |
| `/api/v1/auth/logout`, `/logout/all` (POST) | `/auth/logout`, `/auth/logout/all` | Move under `/v1/auth`. |
| `/api/v1/auth/sessions` (GET), `/auth/sessions/{id}` (DELETE) | `/auth/sessions`, `/auth/sessions/[sessionId]` | Move under `/v1/auth`. |
| `/api/v1/auth/me` (GET) | `/auth/session` | Rename/move to `/v1/auth/me`; drop alias. |
| `/api/v1/auth/email/send`, `/verify` (POST) | `/auth/email/send`, `/auth/email/verify` | Move under `/v1/auth/email`. |
| `/api/v1/auth/password/*` (POST/PATCH) | `/auth/password/...` | Move under `/v1/auth/password`. |
| `/api/v1/auth/service-accounts/*` | `/auth/service-accounts/...` | Move under `/v1/auth/service-accounts`. |
| `/api/v1/auth/signup-policy`, `/register`, `/request-access` | `/auth/signup-policy`, `/auth/register`, `/auth/request-access` | Move under `/v1/auth`. |
| `/api/v1/auth/signup-requests*` | `/auth/signup-requests*` | Move under `/v1/auth`. |
| `/api/v1/auth/invites*` | `/auth/signup-invites*` | Rename path to `/v1/auth/invites`; keep revoke leaf. |
| `/api/v1/chat`, `/chat/stream` (POST) | `/chat`, `/chat/stream` | Move to `/v1/chat`. |
| `/api/v1/agents`, `/agents/{name}/status` (GET) | `/agents`, `/agents/[agentName]/status` | Move to `/v1/agents`. |
| `/api/v1/workflows` (GET), `/workflows/{key}` (GET), `/run`, `/run-stream`, `/runs`, `/runs/{id}`, `/runs/{id}/cancel` | `/workflows`, `/[workflowKey]/run`, `/run/stream`, `/runs`, `/runs/[runId]/cancel` | Move under `/v1/workflows`; adjust `run/stream` to `run-stream`; ensure descriptor GET exists. |
| `/api/v1/conversations*` | `/conversations*` | Move under `/v1/conversations`. |
| `/api/v1/tools` | `/tools` | Move under `/v1/tools`. |
| `/api/v1/containers*` incl. `/agents/{agent_key}/container` | `/containers*`, `/containers/agents/[agentKey]` | Move under `/v1/containers`; rename bind path to include `/container`. |
| `/api/v1/vector-stores*` incl. files and search | `/vector-stores*`, `/vector-stores/create` | Move under `/v1/vector-stores`; drop `/create` alias; verify files/search coverage. |
| `/api/v1/storage/objects*` | `/storage/objects*` | Move under `/v1/storage/objects`. |
| `/api/v1/contact` | `/contact` | Move under `/v1/contact`. |
| `/api/v1/status*` incl. `/status.rss`, `/status/subscriptions/*`, `/status/incidents/{id}/resend`, `/status/subscriptions/verify`, `/challenge` | `/status*`, `/status-subscriptions*` | Consolidate under `/v1/status`; remove alias folder. |
| `/api/v1/billing/*` | `/billing/*` | Move under `/v1/billing`; ensure stream path retained. |
| `/api/v1/tenants/settings` | `/v1/tenants/settings` | Already compliant; verify remains after restructure. |
| `/api/v1/logs` (not in backend) | `/logs` | Decide keep/remove; if internal, document as exception. |
| `/api/v1/test-fixtures/*` (not in backend) | `/test-fixtures/*` | Keep under `/v1/test-fixtures` for e2e, or document as exception. |

### Redirect / alias policy (A2)
- Default stance: remove old unversioned/alias handlers to prevent drift; add explicit `307` redirects only where needed to avoid short-term breakage (e.g., public `status-subscriptions` alias) with TODO to delete.
- Health endpoints remain unversioned to mirror backend (`/health`, `/health/ready`, `/health/storage`); if clients need versioned paths, add thin re-export under `/v1/health` without removing root.
- Non-documented endpoints (`logs`, `test-fixtures`, `health/features`) either move under `/v1/*` and get annotated as internal-only, or are deleted if unused; decision to be finalized before implementation.
- Shared path helper `lib/server/apiPaths.ts` will export `API_V1 = '/api/v1'` and builders for common resources (auth, chat, workflows) to standardize fetch callers.
---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Mapping & Decisions

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Inventory | Produce mapping of current Next API paths → desired `/api/v1` paths using backend doc; flag missing/extra endpoints (health/storage, auth/token, stripe webhook, status aliases, vector-store create). | @platform-foundations | ⏳ |
| A2 | Design guardrails | Decide redirect vs removal strategy for old paths; define shared path helper and naming conventions. | @platform-foundations | ⏳ |
| A3 | Scope exceptions | Document any backend endpoints intentionally not proxied (with rationale) to keep parity expectations explicit. | @platform-foundations | ⏳ |

### Workstream B – Route Handler Migration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Health/Default | Move `/health`, `/health/ready`, add `/health/storage`; resolve `/health/features`; evaluate `/` + `/webhooks/stripe` passthrough. | @platform-foundations | ✅ (storage added; health kept unversioned + mirrored under `/v1`; `/`/webhooks intentionally omitted) |
| B2 | Auth | Rehome all auth routes under `/v1/auth/...`; add `/auth/token` if missing; ensure service-account + signup flows preserve behavior. | @platform-foundations | ✅ |
| B3 | Core Agents/Chat/Workflows | Move chat (incl. stream), agents, tools, workflows (list/run/runs) into `/v1/...`; confirm params match backend keys. | @platform-foundations | ✅ (run-stream path corrected) |
| B4 | Data Surfaces | Shift conversations, logs (if kept), storage, vector-stores (merge `/create`), containers (bind suffix), and contact to `/v1`. | @platform-foundations | ✅ (logs versioned; vector-store create shim redirect) |
| B5 | Status | Replace `status-subscriptions` aliases with `/v1/status/subscriptions` + rss endpoints; align incident resend/challenge/verify paths. | @platform-foundations | ✅ (legacy alias redirects kept temporarily; unsubscribe route removed) |
| B6 | Billing & Tenants | Move billing routes (plans, stream, tenant subscription/usage/events) and tenants/settings into `/v1`; normalize tenantId param casing. | @platform-foundations | ✅ |

### Workstream C – Client Callsites & Tests

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Fetchers/services | Update `lib/api/*`, `lib/server/*`, and feature-specific fetchers/hooks to new `/api/v1` paths; introduce shared base path constant. | @platform-foundations | ✅ (apiPaths helper added; fetchers updated) |
| C2 | UI usage | Update components/actions using `fetch('/api/...')` to versioned paths; remove dead aliases. | @platform-foundations | ✅ (logout buttons, logging beacon, containers, etc.) |
| C3 | Tests | Rewrite route handler tests to hit `/api/v1/...`; add coverage for newly added endpoints (health/storage, missing auth). | @platform-foundations | ✅ (new tests for auth/token, status verify/challenge/delete, health/storage) |
| C4 | Regression | Run pnpm lint/type-check + targeted route tests; add smoke for critical flows (login, chat, billing subscription). | @platform-foundations | ⚠️ (lint/type-check green; broader smoke still outstanding) |

### Workstream D – Documentation & Rollout

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | SNAPSHOT | Update `apps/web-app/SNAPSHOT.md` app/api section to reflect `/v1` layout. | @platform-foundations | ⏳ |
| D2 | Data-access doc | Note new path helper + versioned routes in `docs/frontend/data-access.md` (or adjacent doc) to keep callers aligned. | @platform-foundations | ⏳ |
| D3 | Tracker hygiene | Keep this milestone changelog current; note any intentional omissions/redirects. | @platform-foundations | ⏳ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Plan | Complete inventory + decisions (A1–A3) | Approved mapping + redirect policy | ⏳ | 2025-12-02 |
| P1 – Impl | Execute route moves (B1–B6) + callsite updates (C1–C2) | All handlers under `/v1`, old paths removed/redirected | ⏳ | 2025-12-04 |
| P2 – Validate | Tests/docs (C3–C4, D1–D3) + lint/type-check | Green checks, docs updated | ⏳ | 2025-12-05 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Backend contract reference: `docs/architecture/fast-api-endpoints.md` (source of truth for paths/methods).
- Generated SDK paths in `lib/api/client/sdk.gen` (ensure alignment after route moves; regenerate only if backend spec changes).
- None expected on infra or secrets; uses existing `getServerApiClient` auth.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Consumer breakage from path change | High | Land changes with comprehensive callsite update + tests; consider minimal redirects for highest-traffic endpoints during transition. |
| Missing parity for undocumented endpoints (e.g., `/health/features`) | Med | Decide keep/remove during mapping; document exceptions in tracker. |
| Path/param casing drift (tenantId vs tenant_id) | Med | Add helper for path building; assert params in route tests. |
| Overlooked SDK calls bypassing BFF | Low | Repo-wide grep for `/api/` fetches and direct `client` calls; reconcile during C1/C2. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Automated: `cd apps/web-app && pnpm lint && pnpm type-check`.
- Route tests: update/extend existing `app/api/**/route.test.ts` suites; add cases for `/api/v1/health/storage`, `/api/v1/auth/token` (if added), and status subscription paths.
- Manual spot checks (post-merge): login/logout, chat send + stream, workflow run, billing subscription load, storage upload-url.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags; changes ship immediately after merge. Coordinate with frontend consumers to pull versioned paths.
- If temporary redirects are used, annotate TODOs with removal date to avoid lingering aliases.
- No migrations or env changes expected.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-01 — Routed all Next API handlers under `/api/v1`; added auth/token, status verify/challenge/delete, storage health; merged vector-store create; containers bind path corrected; legacy status-subscription unsub route removed; fetchers/components/tests updated; lint + type-check green.
