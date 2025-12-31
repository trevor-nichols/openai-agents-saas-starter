# Issue Tracker — Tenant Lifecycle Milestone Review

## Summary Table

| ID     | Status | Severity (per reviews)  | Issue                                                                                                                        | Evidence (paths/lines)                                                                                                                                          |
| ------ | ------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TL-001 | Planned | MEDIUM (pre-existing)   | Signup creates tenant in separate transaction → orphan/ownerless tenant on downstream failure                                | `apps/api-service/src/app/services/signup/signup_service.py:166-184`                                                                                            |
| TL-002 | ✅     | HIGH (R1) / MEDIUM (R2) | `support:*` operators blocked from `/platform/*` endpoints (scope mismatch vs docs/tracker)                                  | `apps/api-service/src/app/api/dependencies/platform.py`                                                                                                          |
| TL-003 | ✅     | HIGH (R1) / MEDIUM (R2) | Platform tenant create/update lacks audit activity events (only lifecycle logged)                                            | `apps/api-service/src/app/api/v1/platform/routes_tenants.py`, `apps/api-service/src/app/services/activity/registry.py`                                           |
| TL-004 | ✅     | MEDIUM (R1/R2)          | Slug uniqueness race → DB `IntegrityError` bubbles as 500 (should map to 409)                                                | `apps/api-service/src/app/services/tenant/tenant_account_service.py`, `apps/api-service/src/app/infrastructure/persistence/tenants/account_repository.py`       |
| TL-005 | ✅     | MEDIUM (R1)             | `X-Operator-Override` reused for service-account management and not restricted to read-only operations (policy muddled)      | `apps/api-service/src/app/api/dependencies/service_accounts.py`                                                                                                 |
| TL-006 | ✅     | LOW (R1)                | Tenant self-service exposes `status_reason` (may leak internal operator notes)                                               | `apps/api-service/src/app/api/models/tenant_accounts.py`, `apps/api-service/src/app/api/v1/tenants/routes_account.py`                                           |
| TL-007 | ✅     | LOW (R1)                | `TenantAccountService.finalize_deprovision` has no transition guard                                                          | `apps/api-service/src/app/services/tenant/tenant_account_service.py`                                                                                            |
| TL-008 | ✅     | Missing/Partial (R1)    | Test coverage gaps: platform smoke coverage + specific contract/unit cases missing                                           | See details below (paths listed in R1 Test Notes)                                                                                                               |
| TL-009 | ✅     | BLOCKER                 | New milestone files are untracked and will not ship unless added to git                                                      | Files now tracked (see details below)                                                                                                                          |
| TL-010 | ✅     | Missing (R1/R2)         | Verification/DoD not executed (lint/typecheck/tests not run); migration not verified applied in DB                           | Verification commands run; smoke run failed at `/api/v1/logs` (404); migration apply verified via `just migrate`                                                  |
| TL-011 | ✅     | LOW                      | Smoke coverage matrix missing `/api/v1/platform` row                                                                         | `apps/api-service/tests/smoke/http/COVERAGE_MATRIX.md` (platform row added)                                                                                      |
| TL-012 | ✅     | Nit                     | OpenAPI/SDK regen note location unclear                                                                                       | `docs/frontend/data-access.md` (OpenAPI + SDK regeneration section added)                                                                                       |

---

## Detailed Issues

### TL-001 — Signup transaction risk leaves orphan tenant (MEDIUM — pre-existing/out-of-scope)

* **Finding:** Signup creates tenant account in a separate transaction before owner/user provisioning; failures after this point can leave an active tenant with no owner/rollback path.
* **Evidence:** `apps/api-service/src/app/services/signup/signup_service.py:166-184`
* **Status:** Planned — tracked in `docs/trackers/current_milestones/MILESTONE_SIGNUP_ATOMICITY.md`.
* **Scope note:** Pre-existing and intentionally deferred to a dedicated milestone.
* **Fix direction:** Use a unit-of-work transaction across tenant + user creation, **or** create in a “provisioning” state and finalize after owner creation with cleanup on failure.

### TL-002 — `support:*` scope blocked from platform routes (HIGH R1 / MEDIUM R2)

* **Finding:** `require_platform_operator` only accepts `platform:operator`, contradicting docs/tracker that treat `support:*` as equivalent (support operators get 403s on `/platform/*`).
* **Evidence:** `apps/api-service/src/app/api/dependencies/platform.py` (`R2:21-34`)
* **Fix direction (from reviews):** Allow either scope (e.g., match any of `platform:operator` or `support:*`) or implement a custom dependency using `has_operator_scope`. Add a contract test for `support:*`.

### TL-003 — Missing audit activity events for platform CRUD (HIGH R1 / MEDIUM R2)

* **Finding:** Platform tenant create/update endpoints don’t emit audit activity events; only lifecycle transitions emit tenant.lifecycle events.
* **Evidence:** `apps/api-service/src/app/api/v1/platform/routes_tenants.py` (`R2:68-133`); lifecycle logging referenced via `.../tenant_lifecycle_service.py`
* **Fix direction (from reviews):** Record activity events for create/update (and optionally list/get) including actor metadata; align with milestone DoD expectations.

### TL-004 — Slug collision race not handled (MEDIUM R1/R2)

* **Finding:** Service checks uniqueness but DB unique constraint can still fail under concurrency; `IntegrityError` not handled → 500 instead of 409.
* **Evidence:** `apps/api-service/src/app/services/tenant/tenant_account_service.py` (`R2:110-140`), `apps/api-service/src/app/infrastructure/persistence/tenants/account_repository.py` (`R2:88-131`)
* **Fix direction (from reviews):** Catch `IntegrityError` in repo/service, translate to `TenantAccountSlugCollisionError`, map to 409.

### TL-005 — Operator override policy unclear for service accounts (MEDIUM — Review #1)

* **Finding:** `X-Operator-Override` is reused to authorize service-account management and not restricted to read-only operations; override policy becomes muddled and may enable unexpected mutation paths.
* **Evidence:** `apps/api-service/src/app/api/dependencies/service_accounts.py`
* **Fix direction (from R1):** Use a dedicated operator-auth dependency for service-account admin, or explicitly document + enforce method gating semantics.

### TL-006 — Tenant self-service leaks `status_reason` (LOW — Review #1)

* **Finding:** Tenant-facing response exposes `status_reason`, which may leak internal operator notes.
* **Evidence:** `apps/api-service/src/app/api/models/tenant_accounts.py`, `apps/api-service/src/app/api/v1/tenants/routes_account.py`
* **Fix direction (from R1):** Remove from tenant-facing response or introduce a separate public reason field.

### TL-007 — Missing transition guard for finalize_deprovision (LOW — Review #1)

* **Finding:** `TenantAccountService.finalize_deprovision` has no transition guard; direct calls could skip deprovisioning steps.
* **Evidence:** `apps/api-service/src/app/services/tenant/tenant_account_service.py`
* **Fix direction (from R1):** Validate current status prior to transition or make the method private.

### TL-008 — Test coverage gaps (Missing/Partial — Review #1)

* **Finding(s):**

  * Smoke coverage is partial: self-service only; missing platform CRUD/lifecycle smoke coverage.
  * Missing contract tests for operator override header behavior.
  * Missing unit tests for slug collisions/invalid slugs and for `support:*` operator scope path.
* **Evidence (from R1 Test Notes):**

  * Existing smoke: `apps/api-service/tests/smoke/http/test_tenants_smoke.py` (self-service)
  * Contract: `apps/api-service/tests/contract/test_tenant_accounts_api.py`
  * Unit: `apps/api-service/tests/unit/tenants/test_tenant_account_service.py`, `.../test_tenant_lifecycle_service.py`
  * Tenant dependency unit: `apps/api-service/tests/unit/tenants/test_tenant_dependency.py`

* **Status update:** ✅ Unit + contract tests added for slug collisions, invalid slugs, `support:*` operator scope, and operator override read-only behavior. Smoke coverage added for platform CRUD/lifecycle in `apps/api-service/tests/smoke/http/test_tenants_smoke.py`.
* **Remaining:** Smoke suite executed; failed in observability smoke at `/api/v1/logs` (404) — see TL-010.

### TL-009 — Untracked milestone files (BLOCKER)

* **Finding:** Multiple new milestone deliverables are untracked; they will not ship unless added to git.
* **Status:** ✅ Added to git (staged).
* **Evidence (now tracked):**

  * `apps/api-service/alembic/versions/56d5bfd1fee5_add_tenant_lifecycle_columns.py`
  * `apps/api-service/src/app/api/dependencies/platform.py`
  * `apps/api-service/src/app/api/models/tenant_accounts.py`
  * `apps/api-service/src/app/api/v1/platform/`
  * `apps/api-service/src/app/api/v1/tenants/routes_account.py`
  * `apps/api-service/src/app/services/tenant/tenant_account_service.py`
  * `apps/api-service/src/app/services/tenant/tenant_lifecycle_service.py`
  * `apps/api-service/tests/contract/test_tenant_accounts_api.py`
  * `apps/api-service/tests/unit/tenants/test_tenant_account_service.py`
  * `apps/api-service/tests/unit/tenants/test_tenant_lifecycle_service.py`
  * `apps/api-service/tests/utils/tenant_accounts.py`
  * `docs/trackers/current_milestones/MILESTONE_PLATFORM_TENANT_LIFECYCLE_API.md`

* **Fix direction:** Add all milestone deliverables to git and confirm they are included in the intended release branch.

### TL-010 — Verification/DoD not executed + migration not verified applied (Missing — Reviews #1/#2)

* **Finding(s):**

  * Reviews did not run verification commands (lint/typecheck/tests).
  * Migration lifecycle columns “implemented; not verified applied.”
* **Evidence:**

  * R1: “Commands run: None”; DoD missing
  * R2: “I did not run tests during this review.”
* **Suggested verification commands (from R1):**

  1. `cd apps/api-service && hatch run lint`
  2. `cd apps/api-service && hatch run typecheck`
  3. `cd apps/api-service && hatch run test tests/unit/tenants`
  4. `cd apps/api-service && hatch run test tests/contract/test_tenant_accounts_api.py`
  5. `cd apps/api-service && hatch run test tests/smoke/http/test_tenants_smoke.py` (requires running API server)

* **Status update (2025-12-31):** Lint + typecheck green. Unit + contract tests run. Smoke suite executed and failed at `/api/v1/logs` (404) in `tests/smoke/http/test_observability_smoke.py`. Migration apply verified via `just migrate`.

### TL-011 — Smoke coverage matrix missing platform row (LOW)

* **Finding:** The smoke coverage matrix has no `/api/v1/platform` entry despite the new router.
* **Status:** ✅ Platform row added (marked pending).
* **Evidence:** `apps/api-service/tests/smoke/http/COVERAGE_MATRIX.md`

### TL-012 — OpenAPI/SDK regen note location unclear (Nit — Review #1)

* **Finding(s):**

  * OpenAPI regen + SDK note location unclear (only noted in tracker).
* **Status:** ✅ Note added to frontend data-access doc.
* **Evidence:** `docs/frontend/data-access.md`
