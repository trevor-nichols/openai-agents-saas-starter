<!-- SECTION: Metadata -->
# Milestone: Env Var Contract Standardization

_Last updated: 2026-01-03_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** docs/trackers/analysis/env-vars/analysis/potential_overlap.md, docs/trackers/analysis/env-vars/analysis/unique.md

---

<!-- SECTION: Objective -->
## Objective

Standardize the environment variable contract across the API service, web app, and console by removing aliases/legacy knobs, defining single sources of truth, and aligning tests/docs to prevent config drift.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Canonical env vars adopted: `API_BASE_URL`, `APP_PUBLIC_URL`, `ENABLE_BILLING`, `GCP_PROJECT_ID`, `LOG_ROOT`, `LOGGING_DATADOG_*`, `SIGNUP_ACCESS_POLICY`, `REDIS_URL`.
- Alias/legacy env vars removed from codepaths, docs, tests, and console wizard output.
- Console wizard and ops tooling emit the canonical env set only.
- Web app reads backend feature flags from `/api/health/features` and no longer depends on `NEXT_PUBLIC_ENABLE_BILLING`.
- GCP project IDs standardized with `GCP_PROJECT_ID` + optional `GCP_SM_PROJECT_ID` override.
- All affected tests updated to use canonical env vars.
- `hatch run lint` + `hatch run typecheck` (api-service) and `pnpm lint` + `pnpm type-check` (web-app) and console lint/typecheck are green.
- Docs/trackers updated to reflect the finalized env var contract.
- CI workflows, Docker Compose defaults, and `.env.example` templates aligned to the canonical env set (no legacy knobs).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Remove aliases: `API_URL`, `BACKEND_API_URL`, `NEXT_PUBLIC_API_URL`, `ALLOW_PUBLIC_SIGNUP`, `NEXT_PUBLIC_ALLOW_PUBLIC_SIGNUP`, `PLAYWRIGHT_ALLOW_PUBLIC_SIGNUP`, `NEXT_PUBLIC_ENABLE_BILLING`, `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_VERCEL_URL`, `AUTH_CLI_BASE_URL`, `STATUS_API_BASE_URL`, `ENABLE_*_API_KEY`, `ENABLE_RESEND_EMAIL_DELIVERY`, `AZURE_KEY_VAULT_NAME`, `CONSOLE_LOG_ROOT`, `CONSOLE_LOGGING_DATADOG_*`, `OTEL_EXPORTER_DATADOG_*`, `GCS_PROJECT_ID`, `GCS_SM_*`.
- Implement canonical env usage in API service, web app, console, and ops scripts.
- Update console wizard prompts/output and inventory/schema to match canonical envs.
- Update docs and tests to reflect the new contract.

### Out of Scope
- New feature development or behavioral changes beyond configuration unification.
- Backwards-compat support or migration shims (explicitly not required).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Decisions captured in env-var analysis tracker. |
| Implementation | ✅ | Canonical envs applied across api/web/console/ops. |
| Tests & QA | ✅ | Lint/typecheck green across api/web/console. |
| Docs & runbooks | ✅ | Canonical env contract reflected in docs/templates. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Single source of truth:** `API_BASE_URL` for backend URL; `APP_PUBLIC_URL` for public site URL; `ENABLE_BILLING` for billing; `GCP_PROJECT_ID` for GCP; `LOG_ROOT` + `LOGGING_DATADOG_*` for logging.
- **Alias removal:** eliminate legacy/duplicate env vars to reduce drift; no backwards-compat.
- **Overrides:** keep Redis fan-out overrides as optional (`*_REDIS_URL`), defaulting to `REDIS_URL`; keep `AUTH_SESSION_IP_HASH_SALT` as optional.
- **Frontend feature discovery:** frontend reads billing from `/api/health/features` instead of `NEXT_PUBLIC_ENABLE_BILLING`.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract & Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Docs | Update env-var analysis tracker with decisions (completed). | ✅ |
| A2 | Docs | Update README/env templates and internal docs to canonical envs only. | ✅ |
| A3 | Docs | Update ops/observability docs for Datadog/OTel env naming. | ✅ |
| A4 | Docs | Align `.env.example` templates + CI/Compose defaults with canonical envs; rename API service template to `.env.example`. | ✅ |

### Workstream B – API Service

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Settings | Standardize to `API_BASE_URL`, `APP_PUBLIC_URL`, `GCP_PROJECT_ID`, remove aliases. | ✅ |
| B2 | Email | Replace `ENABLE_RESEND_EMAIL_DELIVERY` with `RESEND_EMAIL_ENABLED` usage in scripts. | ✅ |
| B3 | Providers | Normalize secrets/provider config (drop `GCS_*` Secret Manager envs). | ✅ |

### Workstream C – Web App

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Config | Remove `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_ENABLE_BILLING` usage. | ✅ |
| C2 | Tests | Update Playwright/test harness to use `API_BASE_URL` + `SIGNUP_ACCESS_POLICY`. | ✅ |
| C3 | Health | Ensure billing UI derives from `/api/health/features`. | ✅ |

### Workstream D – Console & Ops

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Console | Remove console-specific logging envs; use `LOG_ROOT` + `LOGGING_DATADOG_*`. | ✅ |
| D2 | Console | Remove `AUTH_CLI_BASE_URL`/`STATUS_API_BASE_URL` in favor of `API_BASE_URL`. | ✅ |
| D3 | Ops | Update collector config to read `LOGGING_DATADOG_*` (drop `OTEL_EXPORTER_DATADOG_*`). | ✅ |

### Workstream E – Tests & QA

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | Tests | Update unit/smoke tests to use canonical env vars. | ✅ |
| E2 | QA | Run lint/typecheck for api/web/console. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Decisions + tracker updates | Decisions recorded, milestone created | ✅ |
| P1 – Implementation | Code + docs updates across stack | All workstreams B–D complete | ✅ |
| P2 – Validation | Tests + lint/typecheck | All checks green, docs updated | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None external. Ensure env-var analysis tracker stays authoritative.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Removing aliases breaks local dev setups | Med | Update all env templates + console wizard output; document changes clearly. |
| Tests fail due to stale env expectations | Low/Med | Update harness + smoke scripts in the same change set. |
| Provider config drift across ops/console | Med | Update ops config renderer and console schema together. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint && hatch run typecheck`
- `cd apps/web-app && pnpm lint && pnpm type-check`
- `cd packages/starter_console && hatch run lint && hatch run typecheck`
- Smoke scripts (as applicable) with canonical envs only.

---

<!-- SECTION: Review Addendum -->
## Review Addendum (2026-01-03)

### Q&A (decisions confirmed)
- **Wizard writes `APP_PUBLIC_URL` into `apps/web-app/.env.local` and adds it to `FRONTEND_ENV_VARS`** — chosen as the best professional approach to keep the web app’s SEO/canonical base URL explicit and consistent across environments.
- **Server-side feature gating uses the BFF route (`/api/health/features`)** — avoids direct fetches from server components to the API service and keeps the boundary consistent with the BFF contract.
- **Untracked files should be committed** — new env/feature helpers, docs, and milestone updates are part of the deliverable.

### Findings logged (to be addressed in this milestone update)
- Missing frontend env propagation: `APP_PUBLIC_URL` not written to `apps/web-app/.env.local` by the wizard.
- Server-side feature gating directly fetched the API service instead of using the BFF route.
- Untracked files required for the milestone were not yet in version control.

### Follow-up actions
- Update wizard frontend section + inventory to emit `APP_PUBLIC_URL` for Next.js.
- Update server-side feature gating to call `/api/health/features` via the BFF.
- Add all milestone artifacts currently untracked to version control.

### Validation Results (2026-01-03)
- `cd apps/web-app && pnpm lint` ✅
- `cd apps/web-app && pnpm type-check` ✅
- `cd packages/starter_console && hatch run lint` ✅
- `cd packages/starter_console && hatch run typecheck` ✅
- `cd apps/api-service && hatch run lint` ✅
- `cd apps/api-service && hatch run typecheck` ✅ (mypy “annotation-unchecked” notes only; no errors)

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No backwards compatibility: remove aliases entirely from configs and docs.
- Regenerate `.env`/wizard outputs to the canonical contract.
- Ensure infra templates (Terraform/ops configs) reference canonical env vars only.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-03 — Milestone created with scope + decisions.
- 2026-01-03 — Implementation + validation complete; lint/typecheck green across api/web/console.
- 2026-01-03 — Review addendum recorded; wizard + BFF follow-ups executed.
