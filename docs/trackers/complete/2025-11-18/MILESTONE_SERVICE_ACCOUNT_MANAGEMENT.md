<!-- SECTION: Title -->
# Service Account Management Milestone

<!-- SECTION: Objective -->
## Objective
Ship tenant-facing auditing and revocation workflows for service-account refresh tokens while preserving operator-only issuance via Vault-signed credentials. The milestone ensures customers can see and manage their machine credentials without escalating to platform staff and that platform responders can still override during incidents.

<!-- SECTION: Background -->
## Background
- Current API surface only exposes `POST /api/v1/auth/service-accounts/issue`, guarded by Vault signatures.
- There is no authenticated list or revoke endpoint, so tenants cannot inspect or disable leaked tokens.
- Repository/service layers already persist service-account tokens and expose `revoke_service_account_token`, but the FastAPI layer and frontend lack entry points.
- Frontend IA (`/(app)/account/service-accounts`) anticipates list/revoke functionality; documenting this milestone aligns roadmap expectations.

<!-- SECTION: Ownership & Permissions -->
## Ownership & Permissions Decisions
1. **Issuance remains operator-only** via Vault-signed CLI calls (status quo). No frontend action for minting.
2. **Tenant-level visibility/revocation**: authenticated tenant admins (or a new `SERVICE_ACCOUNT_ADMIN` role) can list and revoke tokens scoped to their tenant via standard auth dependencies (`require_current_user` + `require_tenant_admin`).
3. **Platform override**: add `require_platform_operator` (or reuse existing operator dependency) so SRE/on-call can supply an audit reason to query/revoke any tenant's tokens during incidents.
4. **Audit trail**: all revoke actions capture `reason`, `actor_type` (tenant_admin vs operator), and timestamp; logs ship to existing observability sinks.
5. **Scope parity**: tenant-admin requests are filtered by `tenant_id`, preventing cross-tenant leakage; operator override bypasses the filter only when the dependency verifies their platform role.

<!-- SECTION: Scope -->
## In Scope
- FastAPI routes
  - `GET /api/v1/auth/service-accounts/tokens`: paginated listing with filters (`account`, `tenant_id`*, `status`, `fingerprint`). `tenant_id` filter ignored for tenant admins (always forced to their tenant); optional for operators.
  - `POST /api/v1/auth/service-accounts/tokens/{jti}/revoke`: accepts `{ "reason": str | None }`, idempotently revokes.
- Pydantic models for the above (request, response, pagination envelope).
- Repository queries & service methods to support listing and revocation metadata (leveraging `ServiceAccountToken` table).
- Frontend hooks/UI updates in `/(app)/account/service-accounts` to surface list + revoke flows (TanStack Query + Shadcn dialogs).
- Starter Console additions (`starter-console tokens list-service-accounts`, `... revoke-service-account`) using authenticated API calls.
- Docs & SNAPSHOT refresh plus this tracker.

## Out of Scope
- Changing Vault issuance flow or adding UI-based issuance.
- Cross-tenant token sharing or delegated scopes per user.
- Token rotation automation jobs (track separately if needed).

<!-- SECTION: Deliverables -->
## Deliverables
- API contract doc + OpenAPI schema updates (regenerated HeyAPI client & types).
- Backend implementation with unit + contract tests covering happy/error paths.
- Frontend service functions, hooks, and screens for browsing/revoking tokens.
- CLI commands with end-to-end tests (fakeredis + sqlite fixtures).
- Observability updates: structured log events for list/revoke, metrics for revoke counts.
- Documentation updates (`docs/frontend/data-access.md`, `SNAPSHOT.md`, CLI tracker).

<!-- SECTION: Workstreams -->
## Workstreams & Checklist
| Workstream | Owner | Tasks | Status |
| ---------- | ----- | ----- | ------ |
| Backend API | Platform Foundations | Design deps, add routes, repository queries, tests | ⧗ In Progress |
| Frontend UI | App Experience | Hook + UI for listing/revoking, empty states | ☐ Not Started |
| CLI | Platform Foundations | CLI list/revoke commands + tests | ☐ Not Started |
| Observability | Infra | Logging/metrics wiring, dashboards | ☐ Not Started |
| Documentation | Platform Foundations | Update SNAPSHOT, data-access doc, release notes | ☐ Not Started |

<!-- SECTION: Implementation Plan -->
## Implementation Plan
1. **Auth Layer**: Implement `require_platform_operator` (if missing) and reusable helper `get_service_account_scope(actor)` returning `(tenant_id, actor_type)`. Wire caching/rate limiting similar to sessions routes.
2. **Repository Enhancements**: Add `list_service_account_tokens` (filters, pagination, include_revoked flag) and extend `RefreshTokenManager` or dedicated repository for service accounts.
3. **Service Layer**: Wrap repository calls in `AuthService` with tenant scoping + actor metadata for logging.
4. **API Routes**: New module `routes_service_account_admin.py` under `app/api/v1/auth/` containing list/revoke endpoints using `SuccessResponse` patterns.
5. **Frontend**: Update HeyAPI generation; create `useServiceAccountTokens` and `useRevokeServiceAccountToken` hooks; integrate into service-accounts page with confirmation modals.
6. **CLI**: Extend `starter_console.commands.auth` to reuse HTTP client config, support pagination, and share revoke confirmation prompts for interactive + headless flows.
7. **Docs/Tracking**: Refresh `SNAPSHOT.md`, data-access doc, and this tracker with status updates; announce in release notes.

<!-- SECTION: Risks -->
## Risks & Mitigations
- **Unauthorized visibility**: Ensure dependencies enforce tenant scoping before hitting the repo; add contract tests proving tenant admins cannot access other tenants.
- **Stale SDK clients**: Coordinate backend merge with HeyAPI regeneration to avoid frontend build failures; enforce CI step.
- **Long-running list queries**: Add indexes (`tenant_id`, `account`, `revoked_at`) if query plans regress; monitor via metrics.
- **Operator misuse**: Require `reason` for operator overrides and emit audit events to SIEM to maintain accountability.

<!-- SECTION: Acceptance Criteria -->
## Acceptance Criteria
- Tenant admin can log in, view their service-account tokens, and revoke one with the action reflected immediately in subsequent queries.
- Operator can list/revoke across tenants only when presenting platform credentials and providing a reason.
- API + CLI + frontend share consistent pagination schema and error messaging.
- Tests cover success, unauthorized, cross-tenant access, and double-revoke scenarios.
- Documentation updated and linked from the service-accounts page.

<!-- SECTION: Timeline -->
## Target Timeline
- Design sign-off: **Nov 18, 2025**