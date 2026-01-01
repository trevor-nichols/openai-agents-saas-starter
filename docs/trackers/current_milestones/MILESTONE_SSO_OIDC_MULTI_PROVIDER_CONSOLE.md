<!-- SECTION: Metadata -->
# Milestone: Multi-Provider OIDC SSO (Console)

_Last updated: 2026-01-01_  
**Status:** Planned  
**Owner:** Platform Foundations / Backend Auth Pod  
**Domain:** Console / Cross-cutting  
**ID / Links:** docs/trackers/current_milestones/MILESTONE_SSO_OIDC_GOOGLE.md, docs/auth/idp.md

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
- `cd packages/starter_console && hatch run lint` and `... typecheck` pass
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Console provider registry with preset metadata (Google, Okta, Microsoft/Azure AD, Auth0)
- Custom OIDC provider path (issuer, discovery, scopes, auth method, ID token algs)
- Wizard: repeatable provider configuration (0..n providers) + summary output
- CLI: `starter-console sso setup` accepts provider key + preset defaults
- Probe: per-provider status checks and summary aggregation
- Documentation updates for multi-provider configuration

### Out of Scope
- Backend schema or API changes
- Frontend SSO UI changes
- SCIM/SAML/IdP-initiated SSO

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⏳ | Requires console registry + env naming scheme decision |
| Implementation | ⏳ | Not started |
| Tests & QA | ⏳ | Not started |
| Docs & runbooks | ⏳ | Not started |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Console owns provider selection + config UX; backend already supports provider_key + config in DB.
- Introduce a console provider registry (preset metadata + defaults) and a custom OIDC path.
- Env naming strategy likely shifts from fixed `SSO_GOOGLE_*` to `SSO_<PROVIDER>_*` with a list of enabled providers (e.g., `SSO_PROVIDERS=google,okta`).
- Seed script already supports `--provider`; console should pass through without backend changes.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Console Registry + CLI

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Console | Provider registry with presets + custom provider schema | ⏳ |
| A2 | Console | `sso setup` accepts arbitrary provider key + preset defaults | ⏳ |
| A3 | Console | Update env writer to support multiple providers | ⏳ |

### Workstream B – Wizard + Probes

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Wizard supports configuring multiple providers | ⏳ |
| B2 | Console | Probe iterates providers and summarizes per-provider status | ⏳ |

### Workstream C – Docs + Tests

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Docs | Update `docs/auth/idp.md` + operator guide | ⏳ |
| C2 | Tests | Unit tests for registry, wizard flows, probe outputs | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Registry + env naming design | Design agreed in tracker | ⏳ |
| P1 – Implementation | CLI + wizard + probes | Multi-provider provisioning works end-to-end | ⏳ |
| P2 – Docs + Tests | Docs + unit tests | All checks green | ⏳ |

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

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- Unit tests for wizard + probes + registry

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Rollout via console-only changes; backend untouched.
- Provide migration guidance for existing `SSO_GOOGLE_*` env vars if naming scheme changes.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-01 — Created milestone for multi-provider OIDC SSO console support.
