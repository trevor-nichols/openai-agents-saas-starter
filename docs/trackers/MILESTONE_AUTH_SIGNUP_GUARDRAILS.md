# AUTH-011 – Signup Guardrails Milestone

_Last updated: November 16, 2025_

## Objective

Reduce the attack surface of `/api/v1/auth/register` by moving the platform toward an invite/approval posture by default, adding operator-grade throttling controls, and ensuring both the FastAPI backend and Starter CLI expose the same guardrails.

## Current Posture (Gap Analysis)

| Area | Status | Notes |
| --- | --- | --- |
| Default exposure | ⚠️ Risk | `allow_public_signup=True` across backend + CLI wizard, so fresh installs ship with open signup. |
| Access controls | ⚠️ Missing | Signup allows any email address; no invite tokens or approval pipeline exist. |
| Throttling | ⚠️ Minimal | Single per-IP quota (`signup_rate_limit_per_hour`); nothing per email/domain/device, no global ceilings, no observability. |
| Operator workflow | ⚠️ Missing | No process or tooling for recording/approving access requests when public signup is disabled. |
| Frontend UX | ⚠️ Missing | Only “Register” CTA; no invite-token input or “Request access” surface tied to backend flows. |

## Phased Plan

| Phase | Focus | Key Deliverables | Target |
| --- | --- | --- | --- |
| P1 – Configuration Guardrails | Settings & CLI defaults favor invite-only deployments while keeping backwards compatibility. | `SignupAccessPolicy` enum in `Settings`, CLI wizard prompt + audit summary, docs updated to flag the insecure default prior to rollout. | Nov 19 |
| P2 – Invite + Approval Workflows | Backend & frontend flows for issuing invites, capturing access requests, and approving them before provisioning tenants. | New persistence models/services, authenticated invite issuance endpoints, `register` requiring tokens when policy != `public`, marketing “Request Access” funnel. | Nov 25 |
| P3 – Throttling & Detection | Multi-bucket rate limiting, structured telemetry, and operational knobs exposed through CLI/Settings. | Per-IP/day + per-email + per-domain quotas, concurrency caps, honeypot/UA fingerprinting hooks, Prometheus metrics + structured logs, docs/runbooks. | Nov 29 |

## Workstreams & Tasks

### WS1 – Policy & Configuration (Phase 1)
- ✅ Introduced `SignupAccessPolicyLiteral = Literal["public", "invite_only", "approval"]` in `app/core/config.py`, defaulting to `"invite_only"` with env alias `SIGNUP_ACCESS_POLICY`. (Nov 16, 2025)
- ✅ `allow_public_signup` now derives from the policy (with conflict warnings for legacy envs). (Nov 16, 2025)
- ✅ CLI wizard prompts for the policy, records it in env/audit output, and keeps `ALLOW_PUBLIC_SIGNUP` in sync for backward compatibility. (Nov 16, 2025)
- ✅ Docs + README updated to document the new policy posture and defaults. (Nov 16, 2025)

### WS2 – Invite & Approval Pipeline (Phase 2)
- ✅ Persistence: `tenant_signup_invites` + `tenant_signup_requests` tables with Alembic revision + SQLAlchemy models. (Nov 16, 2025)
- ✅ Services/APIs:
  - `InviteService` issues/revokes/consumes tokens; `SignupRequestService` stores submissions + approval decisions. (Nov 16, 2025)
  - Auth routes `/api/v1/auth/invites/*`, `/api/v1/auth/signup-requests/*`, and `/api/v1/auth/request-access` enforce new scopes + rate limits. (Nov 16, 2025)
- ✅ Invite reservations: two-phase reserve/finalize flow backed by `tenant_signup_invite_reservations` so failed signups no longer burn tokens; `SignupService` only finalizes the invite after provisioning succeeds. (Nov 16, 2025)
- ✅ Signup flow:
  - `UserRegisterRequest`/frontend accepts `invite_token`; backend policy now requires tokens for invite-only/approval modes. (Nov 16, 2025)
  - Public request-access endpoint persists `tenant_signup_request` rows + structured logs. (Nov 16, 2025)
- Frontend:
  - Add invite-token input + messaging on `/register`.
  - Create “Request Access” flow (feature module under `features/marketing/access-request`) that posts to the new endpoint and confirms submission.

### WS3 – Throttling, Detection & Telemetry (Phase 3)
- Multi-dimensional quotas:
  - `signup_rate_limit_per_ip_hour` (existing) + `signup_rate_limit_per_ip_day`.
  - `signup_rate_limit_per_email_day` and `signup_rate_limit_per_domain_day`.
  - `signup_concurrent_requests_limit` (cap simultaneous outstanding requests per IP).
- Implement reusable helpers in `app/services/rate_limit_service.py` to build compound keys (IP+UA hash) and enforce quotas before hitting DB.
- Add lightweight honeypot field + UA fingerprint hash to `SignupRequest` to slow naïve bots.
- Expose metrics (`signup_attempts_total{result,policy}`, `signup_blocked_total{reason}`) and structured logs to aid detection.
- Update CLI wizard to capture new quota inputs (with sane defaults) and mention telemetry requirements in docs/runbooks.

## Acceptance Criteria
1. Operators can choose between public, invite-only, or approval-required signup modes during setup, with invite-only as the default posture.
2. Invite-only/approval modes enforce token/request validation end-to-end (backend services, API contract, frontend UX, CLI documentation).
3. Signup attempts are throttled by at least three independent quotas (IP/hour, IP/day, email/day) plus concurrency guards, all configurable via environment variables and surfaced through the CLI wizard.
4. Observability: metrics + structured logs exist for successful signups, blocked attempts, invite issuance, and request approvals so Security/Ops can alert on anomalies.
5. Tracker + docs reference the new flow and runbooks (ISSUE_TRACKER entry closed as “Resolved” once all acceptance criteria are met).

## Dependencies & Owners
- **Backend/Auth** (Platform Foundations) — settings, services, APIs, migrations, observability.
- **Starter CLI** (Platform Foundations) — wizard prompts, audit output, docs.
- **Frontend** (Product Web) — register/request-access UX, CTA routing, TanStack queries for invites.
- **Billing** (if plan selection is tied to invites) — confirm handshake for pre-provisioned plans.

## Risks & Mitigations
| Risk | Mitigation |
| --- | --- |
| Token leakage or brute force | Store hashed invite tokens, enforce low TTL, minimum entropy, and revoke on first use. |
| Operator backlog on approvals | Provide CSV/export + CLI batch commands so Ops can triage outside UI; ensure runbooks exist. |
| Legitimate users blocked by quotas | Return descriptive 429 with `Retry-After`, implement allowlist env var for trusted IPs/domains, and document override steps. |
| Frontend/backed contract drift | Add contract tests for new endpoints and update `agent-next-15-frontend` SDK (`pnpm heyapi:generate`) as part of the implementation work. |

## Next Steps
1. Finalize plan review with @anything-agents/auth + CLI owners (this doc).
2. Begin Phase 1 implementation once stakeholders sign off; keep this milestone updated twice weekly until AUTH-011 closes.
