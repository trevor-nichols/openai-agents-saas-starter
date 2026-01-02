<!-- SECTION: Metadata -->
# Milestone: Tenant Identifier Policy & Boundary Enforcement

_Last updated: 2026-01-02_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** [Tenant Identifier Policy](../../auth/tenant-identifier-policy.md)

---

<!-- SECTION: Objective -->
## Objective

Standardize tenant identification by making `tenant_id` the canonical internal identifier,
limiting `tenant_slug` to boundary inputs, and removing all tenant identifier inference from
client flows.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Tenant identifier policy is documented and referenced in auth docs
- SSO boundary inputs require explicit `tenant_id` or `tenant_slug` with no inference
- Login UX makes identifier choice explicit and validates mutual exclusivity
- Tests updated to reflect explicit selection behavior
- `pnpm lint`, `pnpm type-check`, and `pnpm test` pass for the web app
- Tracker updated with final status and changelog

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Policy documentation under `docs/auth`
- Web app SSO/login flow updates to remove inference
- Tests for tenant selector helpers
- Lint/typecheck/test validation for web app

### Out of Scope
- Expanding password login to accept `tenant_slug`
- Backend schema changes or database migration work

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Policy defines explicit boundary and canonical ID usage |
| Implementation | ✅ | Explicit tenant inputs wired through SSO/login UI |
| Tests & QA | ✅ | `pnpm lint`, `pnpm type-check`, `pnpm test` passing |
| Docs & runbooks | ✅ | Policy doc drafted |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Canonical ID is `tenant_id`; `tenant_slug` is allowed only at boundary inputs.
- Web app SSO flows must submit explicit selectors (no UUID guessing).
- Backend remains the source of truth for slug-to-ID resolution.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Documentation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Docs | Add tenant identifier policy to `docs/auth` | ✅ |

### Workstream B – Web App Boundary Enforcement

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | UI | Make tenant identifier input explicit (no inference) | ✅ |
| B2 | Auth | Update tenant selector helpers to require explicit fields | ✅ |

### Workstream C – Tests & QA

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Tests | Update SSO helper tests for explicit selection | ✅ |
| C2 | QA | Run web app lint/type-check/test | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Policy + tracker created | Doc + tracker merged | ✅ |
| P1 – Implementation | Remove inference + UI explicitness | Selector + UI updated, tests adjusted | ✅ |
| P2 – Validation | Lint/type-check/test | All checks green, tracker finalized | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| UX confusion if both identifiers are entered | Low | Explicit labels + validation errors |
| Inconsistent selector usage | Med | Central helper for selection + unit tests |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `pnpm lint`
- `pnpm type-check`
- `pnpm test`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No flags or migrations
- Immediate behavior change for SSO selector input (explicit selection only)

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-02 — Created policy doc and milestone tracker; implemented explicit tenant selection and validated web app checks.
- 2026-01-02 — Linked tenant identifier policy from IdP and SSO runbook docs.
