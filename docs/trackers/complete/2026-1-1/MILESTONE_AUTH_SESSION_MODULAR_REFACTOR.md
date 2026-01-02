<!-- SECTION: Metadata -->
# Milestone: Auth Session Service Modularization

_Last updated: 2026-01-02_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Backend  
**ID / Links:** Internal review, apps/api-service/src/app/services/auth/session_service.py

---

<!-- SECTION: Objective -->
## Objective

Modularize the auth session orchestration internals so token parsing, MFA challenge issuance, and token signing are separated into focused modules while preserving the public API surface and behavior of existing auth services.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `UserSessionService` remains API-compatible (public methods/signatures unchanged).
- Token claim parsing and issuance logic live in dedicated modules with clear interfaces.
- MFA challenge issuance/formatting moved out of the session service.
- No new coupling to infrastructure models in orchestration layer.
- `hatch run lint` and `hatch run typecheck` pass for the API service.
- Auth service README updated to reflect the new module layout.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Introduce auth session token claim parsing module.
- Introduce session token issuance module.
- Extract MFA challenge issuance into a focused helper/service.
- Refactor `UserSessionService` to orchestrate only.
- Update `services/auth/README.md`.

### Out of Scope
- Changes to API routes or response schemas.
- Behavioral changes to token lifetimes or claim shapes.
- Database migrations or persistence model changes.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | OK | Modular boundaries defined and implemented. |
| Implementation | OK | Core refactor complete. |
| Tests & QA | OK | `hatch run lint` and `hatch run typecheck` passed. |
| Docs & runbooks | OK | README updated for module layout. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add `session_claims.py` for refresh/logout/MFA claim parsing.
- Add `session_token_issuer.py` for signing access/refresh tokens.
- Add `mfa_challenge_service.py` for MFA challenge issuance and payload shaping.
- Keep `UserSessionService` as orchestration and persistence facade.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A - Auth Modularization

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Services | Add session claim parsing helpers | Done |
| A2 | Services | Add token issuer module | Done |
| A3 | Services | Add MFA challenge module | Done |
| A4 | Services | Refactor session service to orchestrate only | Done |
| A5 | Docs | Update auth services README | Done |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Claim parsing regressions | Med | Preserve existing error messages and flows; add targeted unit coverage if needed. |
| MFA flow behavior change | Med | Keep payload shape identical; reuse existing signer + settings. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No rollout steps; internal refactor only.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-02 - Milestone created; refactor started.
- 2026-01-02 - Modular services added; session service refactored.
- 2026-01-02 - Lint and typecheck completed.
