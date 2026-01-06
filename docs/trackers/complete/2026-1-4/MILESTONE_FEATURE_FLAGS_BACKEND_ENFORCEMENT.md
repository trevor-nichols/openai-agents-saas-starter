<!-- SECTION: Metadata -->
# Milestone: Backend-Enforced Feature Flags

_Last updated: 2026-01-05_  
**Status:** Review follow-up  
**Owner:** @codex  
**Domain:** Cross-cutting  
**ID / Links:** [docs/trackers/templates/MILESTONE_TEMPLATE.md], [docs/contracts/settings.schema.json], [docs/contracts/settings.md]

---

<!-- SECTION: Objective -->
## Objective

Make feature gating authoritative in the backend with clean, per-tenant entitlements layered under global env switches, and expose a secure feature snapshot for the web app while removing feature flags from public health endpoints.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Backend has a centralized feature evaluation service with explicit rules (env + tenant).
- API routes enforce feature gates via dependencies (fail fast when disabled).
- Feature snapshot is served from an authenticated endpoint (no product flags in health).
- Web app uses backend feature snapshot for UX only; no product flags from `NEXT_PUBLIC_*`.
- Starter Console wizard + inventory align with the new contract and no drift.
- OpenAPI + TS client regenerated; docs updated.
- Post-review remediation items resolved and signed off.
- `hatch run lint` + `hatch run typecheck` (backend), `pnpm lint` + `pnpm type-check` (web), and console lint/typecheck all pass.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Introduce backend FeatureFlag service + typed contracts.
- Add FastAPI feature gate dependencies for billing and other gated features.
- Move feature snapshot to authenticated `/v1/features` endpoint (retire `/health/features`).
- Refactor web app to consume backend feature snapshot for UX.
- Align Starter Console setup wizard + inventory with canonical feature flags.
- Update tests, OpenAPI artifacts, and docs.

### Out of Scope
- Third-party remote flag providers (LaunchDarkly, Unleash, etc.).
- UI redesign or new UI feature work beyond gating UX.
- Backward compatibility shims or aliases (pre-release).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Central feature service + tenant entitlements defined. |
| Implementation | ✅ | Strict auth propagation in billing BFF + optimistic concurrency for tenant settings complete. |
| Tests & QA | ✅ | Lint/typecheck + smoke HTTP suite executed clean. |
| Docs & runbooks | ✅ | Settings + data-access + README refreshed. |
| Remediation | ✅ | Review follow-up items (E8–E9) resolved. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Single backend FeatureFlag service evaluates env gates + tenant entitlements.
- Tenant entitlements stored in `tenant_settings.flags` using reserved `feature.<key>` namespace.
- Effective evaluation = global gate AND (tenant override if set, else inherit global).
- Feature snapshot served from authenticated API endpoint (`/v1/features`) scoped to tenant context.
- Platform operator endpoint manages entitlements (`/v1/platform/tenants/{tenant_id}/features`).
- Health endpoints return operational status only (no product flags).
- Web app uses backend feature snapshot for navigation/UX; backend enforces access.
- Billing plan catalog remains authenticated; public pricing (if needed) should come from a separate, sanitized source.
- Starter Console remains the operator entrypoint for env configuration; no UI-sourced flags.
- Initial product feature keys: `billing`, `billing_stream` (derived from billing + stream env).
- Operational toggles (out of feature service): logging ingest, Slack notifications, retry workers, etc.
- Test-only toggles remain isolated (`SMOKE_ENABLE_*`, `USE_TEST_FIXTURES`, `NEXT_PUBLIC_AGENT_API_MOCK`).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract + Design

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Inventory flags and classify (product vs ops vs test) | @codex | ✅ |
| A2 | API | Define FeatureFlag service contract + evaluation rules | @codex | ✅ |
| A3 | Docs | Update settings contract + remove drifted flags | @codex | ✅ |

### Workstream B – Backend Enforcement

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | API | Implement FeatureFlag service (env + tenant) | @codex | ✅ |
| B2 | API | Add feature-gate dependencies to routers/services | @codex | ✅ |
| B3 | API | Create `/v1/features` endpoint; remove `/health/features` | @codex | ✅ |
| B4 | Tests | Add unit/smoke coverage for feature gates | @codex | ✅ |

### Workstream C – Web App Alignment

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Web | Consume `/api/v1/features` via BFF; update types | @codex | ✅ |
| C2 | Web | Remove product feature gates from env flags | @codex | ✅ |
| C3 | Tests | Update web tests/mocks for new feature endpoint | @codex | ✅ |

### Workstream D – Console + Ops Alignment

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Console | Align wizard prompts + inventory with canonical flags | @codex | ✅ |
| D2 | Console | Update validations for per-tenant entitlements | @codex | ✅ |
| D3 | Docs | Update operator docs + runbooks | @codex | ✅ |

### Workstream E – Post-Review Remediation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Web | Authenticate feature snapshot BFF + return 401 on missing token | @codex | ✅ |
| E2 | API/Web | Preserve `feature.*` entitlements on tenant settings updates + UI hides reserved flags | @codex | ✅ |
| E3 | Tooling | Update OpenAPI guard + regenerate artifacts + SDK | @codex | ✅ |
| E4 | Web | Fix server-side feature flag resolution to avoid auth loss (use server client or forward cookies) + update tests | @codex | ✅ |
| E5 | API | Add contract coverage for feature-gated billing routes returning 403 when disabled | @codex | ✅ |
| E6 | Web | Propagate auth/status codes from `/api/v1/features` BFF (avoid 502 on 401/403) + update tests | @codex | ✅ |
| E7 | API | Prevent entitlement updates from overwriting tenant settings (flags-only persistence) + update tests | @codex | ✅ |
| E8 | Web | Billing BFF routes use strict feature snapshot fetch to propagate auth errors (no fallback masking) + update tests | @codex | ✅ |
| E9 | API/Web | Add optimistic concurrency for tenant settings (`If-Match`/version), return 409 on conflict, update clients/tests | @codex | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Inventory + design decisions | Approved design + flag taxonomy | ✅ |
| P1 – Backend | Feature service + gates + endpoint | API enforced + tests green | ✅ |
| P2 – Web | BFF + UI alignment | UI uses backend snapshot only | ✅ |
| P3 – Console/Docs | Wizard + docs + artifacts | Operator flows aligned | ✅ |
| P4 – QA/Wrap | Lint/typecheck/tests + doc updates | All checks green | ✅ |
| P5 – Remediation | Post-review fixes | All remediation acceptance criteria met | ✅ |

---

<!-- SECTION: Remediation Plan -->
## Remediation Plan (Post-Review)

### Acceptance Criteria
- [x] `/api/v1/features` BFF uses authenticated server client; missing token returns 401; tests updated.
- [x] Tenant settings updates preserve `feature.*` entitlements for non-operators; UI hides reserved flags; tests updated.
- [x] OpenAPI guard updated to require `/api/v1/features`; artifacts + SDK regenerated.
- [x] Server-side feature flag resolution does not drop auth cookies and reflects backend entitlements.
- [x] Billing feature-gate contract test asserts 403 when disabled.
- [x] `/api/v1/features` BFF preserves upstream auth status codes (401/403) instead of returning 502.
- [x] Feature entitlement updates patch flags without clobbering other tenant settings fields.
- [x] Billing BFF routes propagate auth failures (401/403) via strict feature snapshot fetch.
- [x] Tenant settings updates require `If-Match`/version with 409 on conflict; web client updated.
- [x] Backend/web/console lint + typecheck (and relevant tests) green.
- [x] Workstream E + Phase P5 signed off.

### Phase Sign-off Checklist
- [x] P5.1 – Feature snapshot auth + tests complete.
- [x] P5.2 – Entitlement preservation + UI guardrails complete.
- [x] P5.3 – OpenAPI guard + artifacts regeneration complete.
- [x] P5.4 – Billing BFF strict auth propagation + tests complete.
- [x] P5.5 – Tenant settings optimistic concurrency + tests complete.

---

<!-- SECTION: Dependencies -->
## Dependencies

- Existing tenant settings model (for entitlements) or new table if needed.
- OpenAPI + TS SDK regeneration workflow.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Flag drift across services | Med | Centralize evaluation in API + update docs. |
| UI/Backend mismatch | Med | Enforce in API; UI is UX only. |
| Entitlement storage complexity | Low | Start with minimal schema and clear defaults. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `hatch run lint`, `hatch run typecheck`, targeted unit tests.
- Web: `pnpm lint`, `pnpm type-check`, relevant unit tests.
- Console: `cd packages/starter_console && hatch run lint` + `hatch run typecheck`.
- Smoke: run HTTP smoke suite for gated endpoints.

## Validation / QA Execution (2026-01-05)

- Backend: `hatch run lint`, `hatch run typecheck` ✅
- Web: `pnpm lint`, `pnpm type-check` ✅
- Console: `cd packages/starter_console && hatch run lint`, `hatch run typecheck` ✅
- Smoke: `cd apps/api-service && hatch run test tests/smoke/http` ✅
- Test hygiene: renamed `tests/unit/services/test_tenant_settings_service.py` to avoid pytest module collision.

---

<!-- SECTION: Review Follow-up -->
## Review Follow-up (2026-01-05)

- **Concurrency safety (entitlements vs tenant settings):** Feature entitlement updates now patch flags inside a locked repository row to avoid clobbering concurrent tenant settings edits.
- **Reserved flag invariants:** Reserved `feature.*` flags are preserved in `TenantSettingsService` so invariants cannot be bypassed by alternate callers.
- **BFF billing semantics:** Billing BFF routes return `403` when disabled to align with backend gate behavior; navigation still hides billing for UX.

## Review Findings (2026-01-05)

### Findings
- **BFF error envelope consistency:** `/api/v1/features` errors did not follow the standard `ErrorResponse` envelope used elsewhere (success/error/message).
- **Optimistic concurrency contract drift:** `If-Match` is enforced at runtime but marked optional in OpenAPI, so generated SDKs do not require the header.

### Decisions
- **Standardize BFF error envelope:** Return `{ success: false, error, message }` for `/api/v1/features` errors to match the backend error shape.
- **Require `If-Match` in OpenAPI:** Patch the OpenAPI schema to mark `If-Match` as required while keeping `428 Precondition Required` behavior.

### Remediation Actions
- [x] Update `/api/v1/features` BFF error responses to use the standard error envelope; update tests.
- [x] Patch OpenAPI to mark `If-Match` required on `PUT /api/v1/tenants/settings`; add `428` response to schema; regenerate artifacts/SDK.

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Feature gates default to disabled unless explicitly enabled.
- Operators enable features via env + tenant entitlements (wizard-managed).
- Removing `/health/features` is safe pre-release; no legacy shims.

---

<!-- SECTION: Decision Log -->
## Decision Log

- 2026-01-05 — Billing plan catalog remains authenticated (no public billing plans endpoint).
  - Rationale: keeps pricing/entitlement details scoped to authenticated tenant context, avoids data leakage, and preserves a clean separation between operational billing configuration and public-facing marketing content.
  - If public pricing is needed, serve it via a dedicated, sanitized marketing source (static or CMS-backed), not the billing API.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-04 — Milestone created and approved for execution.
- 2026-01-04 — Completed backend enforcement, BFF alignment, console cleanup, docs, and QA.
- 2026-01-04 — Engineering review findings logged; follow-up remediation E4–E5 pending.
- 2026-01-04 — Added post-review remediation plan and phase sign-off checklist.
- 2026-01-04 — Remediation fixes completed (E4–E5) and QA sign-off recorded.
- 2026-01-05 — Added follow-up remediation for strict billing BFF auth propagation + optimistic concurrency.
- 2026-01-05 — Completed E8–E9 remediation: billing BFF strict auth propagation + tenant settings optimistic concurrency.
- 2026-01-05 — Executed lint/typecheck + smoke HTTP suite; resolved pytest module name collision.
