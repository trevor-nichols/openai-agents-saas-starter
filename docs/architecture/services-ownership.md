<!-- SECTION: Title -->
# Service Module Ownership Map

_Last updated: November 17, 2025_

This document captures the current owners and responsibilities for every module under `api-service/src/app/services`. It complements the dependency snapshot (`docs/architecture/services_dependency_snapshot.md`) so refactors stay aligned with clear points of contact.

## Baseline Signals
- Fan-out hotspots today are `auth.builders`, `signup_service`, `auth_service`, and `auth.session_service`, reflecting how identity flows centralize orchestration.
- Fan-in is highest for `user_service`, `auth_service`, `auth.errors`, `stripe_event_models`, and `geoip_service`, so any refactor touching them must involve the owning pod.
- 13 modules are not referenced internally (status, tenant, user, rate limiting) which makes them ideal candidates for the first relocation wave in Phase 2.

## Ownership Table
| Domain | Modules | Owner | Notes |
| --- | --- | --- | --- |
| Conversations & Agents | `agent_service`, `conversation_service` | Platform Foundations · Agent Experience Pod | Owns chat orchestration, SDK sessions, and tool wiring that power `/agents`, `/chat`, and `/conversations` routes. |
| Auth Core | `auth/` (builders, errors, refresh token manager, service_account_service, session_service, session_store), `auth_service` | Platform Foundations · Backend Auth Pod | Guardians for login/session/SA issuance flows plus Redis-backed session store. Coordinate w/ Security for key/claims changes. |
| Signup & Identity Lifecycle | `email_verification_service`, `invite_service`, `password_recovery_service`, `signup_request_service`, `signup_service` | Platform Foundations · Backend Auth Pod (Growth) | Handles public enrollment, invite guardrails, email verification, and recovery workflows. |
| Billing & Stripe | `billing_service`, `billing_events`, `payment_gateway`, `stripe_dispatcher`, `stripe_event_models`, `stripe_retry_worker` | Platform Foundations · Billing Pod | Owns tenant subscriptions, plan orchestration, and all inbound/outbound Stripe event handling (dispatcher, worker, schemas). |
| Status & Notifications | `status_service`, `status_alert_dispatcher`, `status_subscription_service` | Platform Foundations · Status Workstream | Powers `/status` API, alert digests, and subscriber throttling. |
| Tenant Platform | `tenant_settings_service` | Platform Foundations · Tenant Experience Pod | Manages billing contacts, metadata, and webhook settings surfaced in Tenant Settings UI. |
| Users & Directory | `user_service` | Platform Foundations · Backend Auth Pod | Central authority for user CRUD, profile updates, and tenant-user relationships. |
| Shared Services | `rate_limit_service` | Platform Foundations · Shared Services Guild | Provides rate-limit primitives reused by signup and status subscription flows. |
| Integrations | `geoip_service` (Platform Foundations · Observability), `service_account_bridge` (Backend Auth Pod) | Mixed | GeoIP wrappers roll up to Observability; service-account bridge partners with Auth Pod but interacts with onboarding UI. |

## Contact Matrix
- **Agent Experience Pod** – owner of conversations + agent orchestration; first responder for Phase 2 moves touching `agent_service`.
- **Backend Auth Pod** – point of contact for auth core, signup lifecycle, and user directory modules.
- **Billing Pod** – accountable for Stripe-facing logic; must review any relocation of workers/adapters.
- **Status Workstream** – maintains `status_*` modules and coordinates with Marketing for `/status` surfaces.
- **Tenant Experience Pod** – covers tenant settings service.
- **Shared Services Guild** – stewards shared rate-limiting utilities.
- **Observability** – handles GeoIP integrations and related instrumentation.

Escalation order for refactors: contact the owning pod, confirm rollout/test expectations, then proceed with PR scoped to ≤300 LOC per the milestone plan.

## Enforcement
- `pyproject.toml` now bans imports from the legacy flat modules (e.g., `app.services.signup_service`, `app.services.billing_service`). Ruff’s `flake8-tidy-imports` plugin enforces this during `hatch run lint`.
- `api-service/tests/unit/test_service_import_boundaries.py` now scans `apps/api-service/src/app`, `packages/starter_console/`, and `tools/` to guarantee no banned module sneaks in anywhere in the monorepo, giving engineers fast feedback during `pytest` runs.
