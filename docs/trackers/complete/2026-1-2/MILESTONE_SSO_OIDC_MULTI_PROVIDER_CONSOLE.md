<!-- SECTION: Metadata -->
# Milestone: Multi-Provider OIDC SSO (Console)

_Last updated: 2026-01-02_  
**Status:** Complete  
**Owner:** Platform Foundations / Backend Auth Pod  
**Domain:** Console / Cross-cutting  
**ID / Links:** docs/trackers/complete/2026-1-1/MILESTONE_SSO_OIDC_GOOGLE.md, docs/auth/idp.md

---

<!-- SECTION: Objective -->
## Objective

Extend the Starter Console to configure multiple OIDC providers beyond Google via presets and a custom provider path, while keeping the backend provider-agnostic and avoiding schema changes.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Console supports provisioning multiple OIDC providers via a provider registry (Google + major presets + custom)
- Wizard can configure more than one provider in a single run (including tenant/global scope)
- `starter-console sso setup` supports arbitrary provider keys and preset defaults
- Status probe supports multiple providers and reports per-provider state
- Docs updated (operator guide + idp.md) with multi-provider guidance
- Console tests updated/added for registry, wizard flows, and probes
- Postgres enforces provider key format + lowercase for SSO tables; seed script validates provider_key
- `cd packages/starter_console && hatch run lint` and `... typecheck` pass
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Console provider registry with preset metadata (Google, Okta, Azure/Entra, Auth0)
- Custom OIDC provider path (issuer, discovery, scopes, auth method, ID token algs)
- Wizard: repeatable provider configuration (0..n providers) + summary output
- CLI: `starter-console sso setup` accepts provider key + preset defaults
- Probe: per-provider status checks and summary aggregation
- Documentation updates for multi-provider configuration
- Backend: Postgres-only provider_key constraints + normalization guardrails for SSO tables
- Backend: seed_sso_provider validation aligned with provider_key policy

### Out of Scope
- Backend API changes beyond provider_key constraints
- Frontend SSO UI changes
- SCIM/SAML/IdP-initiated SSO

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Registry shape, env naming, and preset template approach locked |
| Implementation | ✅ | Multi-provider console flow complete |
| Tests & QA | ✅ | Unit coverage updated; lint/typecheck green |
| Docs & runbooks | ✅ | IdP doc + console guide updated |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Console owns provider selection + config UX; backend already supports provider_key + config in DB.
- Introduce a console provider registry (preset metadata + defaults + human-readable labels) and a custom OIDC path.
- Env naming strategy uses `SSO_<PROVIDER>_*` keys with a required `SSO_PROVIDERS=google,azure,...` list (authoritative; may be empty).
- `SSO_PROVIDERS` is the sole source of enabled providers; per-provider `SSO_<PROVIDER>_ENABLED` is informational only and mismatches should warn.
- Presets ship issuer/discovery URL templates containing `{placeholder}` tokens and enforce replacement before seeding.
- Provider keys are normalized to lowercase `[a-z0-9_]+` to keep env vars safe and consistent.
- Postgres enforces provider_key format and lowercase via CHECK constraints to prevent drift.
- Seed script already supports `--provider`; console should pass through without backend changes.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Console Registry + CLI

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Console | Provider registry with presets + custom provider schema | ✅ |
| A2 | Console | `sso setup` accepts arbitrary provider key + preset defaults | ✅ |
| A3 | Console | Update env writer to require `SSO_PROVIDERS` | ✅ |

### Workstream B – Wizard + Probes

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Wizard supports configuring multiple providers | ✅ |
| B2 | Console | Automation seeds multiple providers from `SSO_PROVIDERS` | ✅ |
| B3 | Console | Probe iterates providers and summarizes per-provider status | ✅ |

### Workstream C – Docs + Tests

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Docs | Update `docs/auth/idp.md` + operator guide | ✅ |
| C2 | Tests | Unit tests for registry, wizard flows, probe outputs | ✅ |

### Workstream D – Review Fixes (Post-Review Hardening)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Console | Default unknown provider keys to the custom preset (no Google fallback). | ✅ |
| D2 | Console | Reserve `custom` as preset-only; reject it as a provider key in CLI, wizard, and `SSO_PROVIDERS`. | ✅ |
| D3 | Console | Ensure `SSO_PROVIDERS` represents enabled providers only (reconcile list vs flags). | ✅ |
| D4 | Tests | Add unit tests for provider registry + provider-key validation edge cases. | ✅ |
| D5 | Repo hygiene | Ensure new registry module is tracked and imported consistently. | ✅ |
| D6 | Cleanup | Retire or align stale helper paths (e.g., `resolve_default_config`) to avoid reintroducing Google defaults. | ✅ |
| D7 | Console | Treat `SSO_PROVIDERS` as authoritative (even when empty) and ignore per-provider `ENABLED` for enablement; warn on mismatches. | ✅ |
| D8 | Tests | Add unit coverage for empty `SSO_PROVIDERS` and list-vs-flag mismatch behavior. | ✅ |

### Workstream E – Backend DB Hardening (Provider-Key Integrity)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | Backend | Add Postgres-only CHECK constraints for provider_key format + lowercase (sso_provider_configs, user_identities) with preflight guardrails. | ✅ |
| E2 | Backend | Align seed_sso_provider validation with provider_key policy. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Registry + env naming + preset template design | Design agreed in tracker | ✅ |
| P1 – Implementation | Registry + CLI + env updates | Multi-provider CLI provisioning works end-to-end | ✅ |
| P2 – Implementation | Wizard + automation + probes | Multi-provider wizard/probes work end-to-end | ✅ |
| P3 – Docs + Tests | Docs + unit tests | All checks green | ✅ |
| P4 – DB Hardening | Provider-key constraints + seed validation | Constraints + script validation merged; lint/typecheck green | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- MILESTONE_SSO_OIDC_GOOGLE.md completed and merged

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Env naming complexity | Med | Adopt `SSO_PROVIDERS` list + `SSO_<PROVIDER>_*` keys; validate in console | 
| UX overload in wizard | Med | Keep presets + advanced fields behind optional prompts | 
| Backward compatibility for existing `SSO_GOOGLE_*` | Low | Provide migration note in docs; optional alias support in console | 
| Uppercase/invalid provider keys already stored | Low | Preflight collision check + normalize to lowercase before adding CHECK constraints |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- Unit tests for wizard + probes + registry
- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`

---

<!-- SECTION: Review Findings -->
## Review Findings & Decisions (2026-01-02)

- **Finding:** Wizard automation could seed preset template placeholders when defaults are used (headless runs with `SSO_PROVIDERS` + missing issuer/discovery).  
  **Decision:** Enforce template placeholder validation in the shared env config builder and reuse the helper across CLI + wizard to prevent invalid seeds.
- **Finding:** Migration preflight did not explicitly guard against invalid provider_key formats before adding CHECK constraints.  
  **Decision:** Add preflight queries that fail fast with a clear error when invalid characters exist.
- **Decision:** Backend services and scripts remain provider-agnostic; the `custom` key is reserved only in console UX (`SSO_PROVIDERS`, CLI, wizard), and docs reinforce the policy.
- **Decision:** Backend CLI scripts emit a lightweight warning when `provider_key=custom` to steer operators toward a distinct key without enforcing a hard block.
- **Note:** Unrelated storage unit-test refactor was intentional and tracked separately.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Rollout via console-only changes; backend untouched.
- Provide migration guidance for existing `SSO_GOOGLE_*` env vars if naming scheme changes.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-01 — Created milestone for multi-provider OIDC SSO console support.
- 2026-01-02 — Alignment complete: `SSO_PROVIDERS` required, provider keys normalized, Azure/Entra standardized, preset URL templates with required placeholder replacement.
- 2026-01-02 — Phase 1 complete: registry + CLI + `SSO_PROVIDERS` updates wired (lint/typecheck green).
- 2026-01-02 — Phase 2 complete: wizard, automation seeding, and multi-provider probes wired (lint/typecheck green).
- 2026-01-02 — Phase 3 complete: docs + unit tests updated (lint/typecheck green).
- 2026-01-02 — Review addendum: `SSO_PROVIDERS` required + authoritative (even empty); list-vs-flag mismatch should warn; follow-up implementation/tests queued.
- 2026-01-02 — Review addendum implemented: authoritative empty list behavior + mismatch warnings tested.
- 2026-01-02 — Added DB hardening workstream: provider_key CHECK constraints + seed validation.
- 2026-01-02 — DB hardening complete: Postgres provider_key constraints added + seed script validation aligned (lint/typecheck green).
- 2026-01-02 — Alembic adjustment: tenant_role enum creation in SSO migration set to `create_type=False` to avoid duplicate type errors.
- 2026-01-02 — Review follow-ups: placeholder validation added to env-based SSO config, migration preflight tightened, decisions documented.
