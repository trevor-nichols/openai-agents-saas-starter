<!-- SECTION: Title -->
# Services Architecture Milestone — Domain Modules

_Last updated: November 17, 2025_

## Objective
Establish a documented, phased plan to restructure `anything-agents/app/services` into domain-scoped modules that mirror API routers and repository boundaries. The milestone completes when every service lives in a clearly owned domain package, imports remain ergonomic, and the reorg is backed by automated checks plus rollout guardrails.

## Success Criteria
- Directory structure expresses bounded contexts (Auth, Billing, Conversations, Signup, Status, Tenant, Shared) with ≤5 files per leaf folder.
- Public imports stay stable via package façades (e.g., `from app.services.billing import BillingService`).
- Each domain exposes an explicit `__all__` and README that outlines responsibilities and dependencies.
- CI enforces import boundaries via `ruff` rules + architectural tests.
- Migration plan is tracked and executed incrementally without blocking ongoing feature work.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Directory clarity | ⚠️ Fragmented | 20+ flat modules with only Auth nested, obscuring ownership.
| Cross-domain coupling | ⚠️ Moderate | Payment/billing helpers intermixed with user + signup flows.
| Tests | ⚠️ Sparse | No architectural tests enforcing module access.
| Developer onboarding | ⚠️ Slow | New contributors rely on tribal knowledge to find orchestration logic.
| Tooling support | ⚠️ Missing | No lint or docs guardrails around service boundaries.

## Target Service Architecture
The end-state structure groups orchestration logic by domain and separates integration façades. Each folder gets an `__init__.py` that exports the stable API and an optional `README.md` for context.

```text
anything-agents/app/services/
  __init__.py                    # Barrel file exporting domain façades
  shared/
    __init__.py
    rate_limit_service.py
  auth/
    __init__.py
    builders.py
    errors.py
    refresh_token_manager.py
    service_account_service.py
    session_service.py
    session_store.py
  billing/
    __init__.py
    billing_service.py
    billing_events.py
    payment_gateway.py
    stripe/
      __init__.py
      dispatcher.py
      event_models.py
      retry_worker.py
  conversations/
    __init__.py
    agent_service.py
    conversation_service.py
  signup/
    __init__.py
    invite_service.py
    signup_service.py
    signup_request_service.py
    email_verification_service.py
    password_recovery_service.py
  status/
    __init__.py
    status_service.py
    status_alert_dispatcher.py
    status_subscription_service.py
  tenant/
    __init__.py
    tenant_settings_service.py
  users/
    __init__.py
    user_service.py
  integrations/
    __init__.py
    service_account_bridge.py
    geoip_service.py
```

### Guiding Principles
1. **Domain mirrors API**: v1 routers and repositories share names with service folders to make navigation trivial.
2. **Façade exports**: Keep import ergonomics by exporting top-level classes/functions from package `__all__` definitions.
3. **Shared utilities stay minimal**: Only primitives reused across domains live under `shared/`.
4. **Integrations isolated**: Third-party adapters (Stripe, GeoIP, bridges) remain in `integrations/` until we can push them deeper into `infrastructure/`.

## Phased Plan
| Phase | Scope | Deliverables | Owner | Target |
| --- | --- | --- | --- | --- |
| 0. Baseline | Capture current imports, add module ownership doc, set up tracker. | This tracker, dependency graph via `scripts/moduleviz.py`. | Platform Foundations | Nov 19 |
| 1. Domain Scaffolding | Create domain folders (`billing`, `signup`, etc.), add README + `__init__` barrels, wire `ruff` `per-file-ignores` for temporary mixing. | Empty folders + docs committed, no code moves yet. | Platform Foundations | Nov 21 |
| 2. Low-Risk Moves | Relocate purely internal modules (status, tenant, user, shared) with import re-exports; run `hatch run lint`/`typecheck`. | PR with path moves + updated imports + docs. | Platform Foundations | Nov 26 |
| 3. High-Risk Moves | Split billing/Stripe and signup/auth flows; ensure async workers + background tasks updated. | PR with billing/signup migrations, new architectural tests. | Platform Foundations | Dec 3 |
| 4. Tooling & Enforcement | Add `ruff` `flake8-tidy-imports` rules, pytest import tests, and docs updates. | CI rules + developer README updates. | Platform Foundations | Dec 5 |
| 5. Hardening | Audit notebooks/scripts for stale imports, update `SNAPSHOT.md`, host brown-bag walkthrough. | Updated snapshots, recorded demo. | Platform Foundations | Dec 8 |

## Dependencies & Coordination
- Coordinate with Backend Infra before moving Stripe workers so deployment scripts stay aligned.
- Update `docs/openai-agents-sdk/services.md` if references point to old paths.
- Keep Frontend in the loop for any import alias renames consumed by server actions.

## Risk Log
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Circular imports during transition | Medium | Phase 1 adds barrels + shared folder before relocating code. Use module graph checks per PR. |
| Long-lived feature branches | Medium | Enforce sub-phase PRs (≤300 LOC) to keep rebases light. |
| Missed runtime worker configs | High | Add checklist entry for Celery/worker entrypoints referencing `stripe_retry_worker`. |
| Docs drift | Medium | Require `SNAPSHOT.md` + tracker updates as part of Definition of Done. |

- **2025-11-17**: Phase 5 (hardening) completed — repo-wide scan confirms no stale imports (CLI/scripts included), dependency snapshot refresh verified, and docs capture the enforcement story so future contributors understand the guardrails.
- **2025-11-17**: Phase 4 (tooling & enforcement) completed — Ruff bans direct imports of the old flat modules via `flake8-tidy-imports`, and `tests/unit/test_service_import_boundaries.py` guards the rule at runtime; docs updated to describe the enforcement.
- **2025-11-17**: Phase 3 (high-risk moves) landed — billing modules (service, events, gateway, Stripe dispatcher/worker/event models) now live under `services/billing/**`, signup/identity flows (`email_verification_*`, invites, password recovery, signup requests/service) live under `services/signup/**`, import sites updated, barrels populated, `SNAPSHOT.md` refreshed, dependency snapshot regenerated, and `hatch run lint` + `hatch run typecheck` executed.
- **2025-11-17**: Phase 2 (low-risk moves) completed — relocated status, shared (rate limit), tenant settings, and user services into their domain packages, added barrel exports, refreshed `SNAPSHOT.md`, regenerated the dependency snapshot, and reran `hatch run lint` + `hatch run typecheck` to lock in the new import paths.
- **2025-11-17**: Phase 1 scaffolding completed — domain folders (`billing`, `billing/stripe`, `conversations`, `signup`, `status`, `tenant`, `users`, `shared`, `integrations`) now exist with README + barrel files, and `pyproject.toml` gained a targeted Ruff per-file-ignore for transitional imports. Dependency snapshot regenerated to capture the new packages.
- **2025-11-17**: Phase 0 baseline completed — added `scripts/moduleviz.py`, captured `docs/architecture/services_dependency_snapshot.md`, and published ownership map in `docs/architecture/services-ownership.md`.
- **2025-11-17**: Initial milestone drafted; awaiting review before Phase 0 kickoff.
