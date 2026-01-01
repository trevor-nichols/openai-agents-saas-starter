<!-- SECTION: Metadata -->
# Milestone: Signup Atomicity + Tenant Provisioning Safety (API)

_Last updated: 2025-12-31_  \
**Status:** Complete  \
**Owner:** Platform Foundations  \
**Domain:** Backend  \
**ID / Links:** [TL-001], [apps/api-service/src/app/services/signup/signup_service.py]

---

<!-- SECTION: Objective -->
## Objective

Eliminate orphan/ownerless tenant accounts created during signup by ensuring tenant + owner creation is
atomic and auditable, with deterministic rollback or cleanup on failure.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Signup flow creates tenant + owner within a single unit-of-work transaction **or** uses a provisioning
  state with explicit finalize/rollback.
- No orphan tenant accounts remain after signup failures (verified by unit tests).
- Error mapping returns stable, user-friendly responses for failure cases.
- Unit + contract tests cover failure paths (tenant create, user create, billing provision).
- `hatch run lint`, `hatch run typecheck`, and relevant tests pass.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Signup orchestration (`services/signup`) transaction boundaries or provisioning state.
- Tenant account service changes required to support atomicity.
- Tests and docs updates for signup safety.

### Out of Scope
- Broader tenant lifecycle model changes beyond what atomicity requires.
- Async provisioning workflows or background jobs.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Explicit provisioning state for tenant + owner; billing occurs after commit. |
| Implementation | ✅ | Tenant starts `provisioning`, owner starts `pending`, promotion after billing success. |
| Tests & QA | ✅ | Unit + contract coverage added for register failure mappings. |
| Docs & runbooks | ✅ | Signup README aligned with provisioning + billing failure behavior. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Implemented: unit-of-work transaction across tenant account + owner creation in `SignupService`.
- Implemented: explicit `provisioning` status for tenants; owner starts `pending` and is promoted to `active` after billing succeeds.
- Billing failure now marks the tenant deprovisioned and disables the owner user (fail closed).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Design + Alignment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Design | Choose transaction vs provisioning state approach. | ✅ |
| A2 | Domain | Document required domain/service changes. | ✅ |

### Workstream B – Implementation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Service | Implement atomic signup flow. | ✅ |
| B2 | Error Handling | Ensure stable error mapping for failure cases. | ✅ |

### Workstream C – Tests + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Tests | Add unit/contract tests for failure paths. | ✅ |
| C2 | Docs | Update relevant docs/trackers. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Decide approach + update tracker. | Approach locked. | ✅ |
| P1 – Implementation | Atomic signup changes implemented. | Tests green. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Tenant account service + repository patterns.
- Existing signup flow and auth service behavior.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Billing failure leaves tenant/user created. | Medium | Mitigated: fail closed by deprovisioning tenant and disabling owner. |
| Regression in signup UX. | Medium | Add contract tests + keep error mapping stable. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/unit/accounts/test_signup_service.py`
- `cd apps/api-service && hatch run test tests/unit/tenants/test_tenant_dependency.py`
- `cd apps/api-service && hatch run test tests/unit/tenants/test_tenant_account_service.py`
- `cd apps/api-service && hatch run test-contract`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags.
- If regression occurs, revert signup orchestration change first.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-31 — Tracker created from TL-001 follow-up.
- 2025-12-31 — Implemented provisioning state + fail-closed billing behavior; docs aligned.
- 2025-12-31 — Added contract coverage for register failure mappings; milestone complete.
