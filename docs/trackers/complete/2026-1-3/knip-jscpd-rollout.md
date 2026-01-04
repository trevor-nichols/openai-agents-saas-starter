<!-- SECTION: Metadata -->
# Milestone: Knip + jscpd Guardrails Rollout

_Last updated: 2026-01-04_  
**Status:** Completed  
**Owner:** @frontend  
**Domain:** Cross-cutting  
**ID / Links:** apps/web-app, apps/api-service, package.json

---

<!-- SECTION: Objective -->
## Objective

Introduce unused-code and duplication guardrails with Knip (web-app) and jscpd (repo-wide) using a phased rollout: local baseline first, CI advisory next, and enforcement once tuned.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Knip configured for `apps/web-app` with Next.js plugin and ignores for generated output
- jscpd configured at repo root with TS/JS/Python scope and tuned ignore list
- Package scripts added for local runs (`lint:knip`, `lint:jscpd`)
- CI runs Knip for the web app and publishes jscpd report (advisory or enforced per phase)
- `pnpm lint`, `pnpm type-check`, `pnpm lint:knip`, and `pnpm lint:jscpd` pass
- Tracker updated with phase sign-offs

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add Knip config + script to `apps/web-app`
- Add jscpd config + script at repo root
- Wire CI checks for Knip and jscpd
- Tune ignore lists for generated files, artifacts, and tests

### Out of Scope
- Refactor or delete existing unused code
- Deduplicate existing code flagged by jscpd
- Backend schema or API changes

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Rollout plan defined with phased enforcement. |
| Implementation | ✅ | Local + CI rollout complete. |
| Tests & QA | ✅ | Phase checks complete; Knip/jscpd runs verified. |
| Docs & runbooks | ✅ | Tracker updated through completion. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Knip runs inside `apps/web-app` with the Next.js plugin to accurately resolve App Router entries.
- jscpd runs at repo root to scan TS/JS and Python while ignoring generated code, artifacts, and tests.
- CI uses advisory reporting for jscpd initially to establish a baseline, while Knip is eligible for gating once clean.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Local Baseline

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Config | Add Knip + jscpd config files | ✅ |
| A2 | Scripts | Add lint scripts + dependencies | ✅ |
| A3 | QA | Run lint/type-check + new tool runs | ✅ |

### Workstream B – CI Advisory

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | CI | Add Knip step to frontend CI | ✅ |
| B2 | CI | Add jscpd job + artifact output (advisory) | ✅ |
| B3 | QA | Run lint/type-check after CI wiring | ✅ |

### Workstream C – Enforcement

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Scripts | Add Knip to web-app validate flow | ✅ |
| C2 | CI | Decide jscpd enforcement/threshold | ✅ |
| C3 | QA | Final lint/type-check + jscpd run | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Tracker + rollout plan | Tracker created and scoped | ✅ |
| P1 – Local baseline | Config + scripts + deps | Knip/jscpd run locally; lint/type-check pass | ✅ |
| P2 – CI advisory | CI wiring | Knip runs in CI; jscpd report published | ✅ |
| P3 – Enforcement | Validate flow + thresholds | Knip enforced; jscpd policy finalized | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (frontend tooling only)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Noisy false positives | Med | Tune ignore lists + thresholds before enforcing. |
| CI time increase | Low | Keep jscpd advisory and scoped to code extensions. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- `cd apps/web-app && pnpm lint:knip`
- `pnpm lint:jscpd`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Roll out completed: Knip enforced in validate + CI; jscpd remains advisory with report artifacts.
- Enforce jscpd only after a dedicated de-duplication milestone and threshold sign-off.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-04 — Tracker created and P0 alignment completed.
- 2026-01-04 — P1 baseline complete: configs + scripts + deps; lint/type-check/knip/jscpd run.
- 2026-01-04 — P2 CI advisory complete: Knip step added; jscpd report job added.
- 2026-01-04 — P3 enforcement complete: Knip added to validate; jscpd policy finalized.
- 2026-01-04 — jscpd ignore list tuned for tests/docs/stories; baseline report captured.
