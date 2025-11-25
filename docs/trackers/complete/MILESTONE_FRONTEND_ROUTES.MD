---
title: Frontend Route Parity Milestone
owner: Platform Foundations
last_updated: 2025-11-10
status: completed
tags:
  - frontend
  - milestones
  - api-parity
---

# Frontend Route Parity Milestone

## Goal

Bridge every backend HTTP endpoint documented in `api-service/src/app/api/ENDPOINTS.md` with a production-ready entry point in the Next.js frontend so web clients and server actions never need to bypass the App Router layer.

## Scope

- ✅ Include: App Router API routes, server actions, and supporting service helpers that proxy backend functionality.
- ✅ Include: Associated UI hooks/components required to expose newly available data.
- ✅ Include: Vitest unit tests, Playwright coverage updates, and configuration tweaks necessary for parity.
- ❌ Exclude: Direct edits to HeyAPI generated artifacts. Capture generator gaps in `docs/trackers/ISSUE_TRACKER.md`.
- ❌ Exclude: Backend implementation defects (track separately).

## Current Coverage Snapshot (2025-11-10)

### Routes Delivered

| Backend | Frontend Entry Point | Coverage Notes |
| --- | --- | --- |
| `POST /api/v1/auth/token` | `app/actions/auth.ts::loginAction` | Exchanges credentials via `loginWithCredentials`; persists cookies. |
| `POST /api/v1/auth/refresh` | `app/api/auth/refresh/route.ts` | Rotates tokens with `refreshSessionWithBackend`. |
| `GET /api/v1/auth/me` | `app/api/auth/session/route.ts` | Returns session summary and profile via `getCurrentUserProfile`. |
| `POST /api/v1/chat/stream` | `app/api/chat/stream/route.ts` | Streaming bridge through `openChatStream`. |
| `GET /api/v1/conversations` | `app/api/conversations/route.ts` | Lists conversations via server action; Vitest coverage in place. |
| `GET /api/v1/tools` | `app/api/tools/route.ts` | Proxies `listAvailableTools`. |
| `GET /api/v1/billing/plans` | `app/api/billing/plans/route.ts` | Serves billing plan catalog. |
| `GET /api/v1/billing/stream` | `app/api/billing/stream/route.ts` | SSE passthrough with tenant role header support. |
| `GET /health` | `app/api/health/route.ts` | New proxy returns backend liveness payload; Vitest coverage added. |
| `GET /health/ready` | `app/api/health/ready/route.ts` | New proxy returns backend readiness payload; Vitest coverage added. |
| `POST /api/v1/chat` | `app/api/chat/route.ts` | Non-streaming proxy returning agent responses; Vitest coverage added. |
| `GET /api/v1/conversations/{conversation_id}` | `app/api/conversations/[conversationId]/route.ts` | Detail proxy returning full history; Vitest coverage added. |
| `DELETE /api/v1/conversations/{conversation_id}` | `app/api/conversations/[conversationId]/route.ts` | Delete proxy clearing stored history; Vitest coverage added. |
| `GET /api/v1/agents` | `app/api/agents/route.ts` | Inventory proxy listing agents; Vitest coverage added. |
| `GET /api/v1/agents/{agent_name}/status` | `app/api/agents/[agentName]/status/route.ts` | Status proxy returning agent telemetry; Vitest coverage added. |
| `GET /api/v1/billing/tenants/{tenant_id}/subscription` | `app/api/billing/tenants/[tenantId]/subscription/route.ts` | Subscription detail proxy with unit coverage. |
| `POST /api/v1/billing/tenants/{tenant_id}/subscription` | `app/api/billing/tenants/[tenantId]/subscription/route.ts` | Subscription start proxy with unit coverage. |
| `PATCH /api/v1/billing/tenants/{tenant_id}/subscription` | `app/api/billing/tenants/[tenantId]/subscription/route.ts` | Subscription update proxy with unit coverage. |
| `POST /api/v1/billing/tenants/{tenant_id}/subscription/cancel` | `app/api/billing/tenants/[tenantId]/subscription/cancel/route.ts` | Subscription cancel proxy with unit coverage. |
| `POST /api/v1/billing/tenants/{tenant_id}/usage` | `app/api/billing/tenants/[tenantId]/usage/route.ts` | Usage record proxy with unit coverage. |
| `POST /api/v1/auth/logout` | `app/api/auth/logout/route.ts` | Logout proxy clears cookies; Vitest coverage added. |
| `POST /api/v1/auth/logout/all` | `app/api/auth/logout/all/route.ts` | Logout-all proxy clears cookies; Vitest coverage added. |
| `GET /api/v1/auth/sessions` | `app/api/auth/sessions/route.ts` | Session list proxy with query support; Vitest coverage added. |
| `DELETE /api/v1/auth/sessions/{session_id}` | `app/api/auth/sessions/[sessionId]/route.ts` | Session revoke proxy; Vitest coverage added. |
| `POST /api/v1/auth/email/send` | `app/api/auth/email/send/route.ts` | Email verification send proxy; Vitest coverage added. |
| `POST /api/v1/auth/email/verify` | `app/api/auth/email/verify/route.ts` | Email verification confirm proxy; Vitest coverage added. |
| `POST /api/v1/auth/password/forgot` | `app/api/auth/password/forgot/route.ts` | Password reset request proxy; Vitest coverage added. |
| `POST /api/v1/auth/password/confirm` | `app/api/auth/password/confirm/route.ts` | Password reset confirmation proxy; Vitest coverage added. |
| `POST /api/v1/auth/password/change` | `app/api/auth/password/change/route.ts` | Password change proxy; Vitest coverage added. |
| `POST /api/v1/auth/password/reset` | `app/api/auth/password/admin-reset/route.ts` | Admin password reset proxy; scope-guarded with Vitest coverage. |
| `POST /api/v1/auth/service-accounts/issue` | `app/api/auth/service-accounts/issue/route.ts` | Service-account issuance proxy; Vitest coverage added. |
| `POST /api/v1/auth/register` | `app/api/auth/register/route.ts` | Tenant registration proxy that persists session cookies; Vitest coverage added. |

### Gaps To Close

| Area | Status |
| --- | --- |
| API Parity | ✅ Complete — all documented backend routes now have frontend proxies/actions. |

## Workstreams & Next Actions

### 1. Health Proxy (Completed 2025-11-10)
- `lib/server/services/health.ts` with typed responses.
- App Router proxies (`app/api/health/*`) and Vitest coverage in place.

### 2. Auth Lifecycle Extensions (Completed 2025-11-10)
- Auth service helpers split by concern; proxy routes + server actions live with tests.

### 3. Agent Inventory Surface (Completed 2025-11-10)
- `lib/server/services/agents.ts` now surfaces list + status helpers.
- App Router proxies (`app/api/agents/*`) live with Vitest coverage.
- Added `useAgents` hook and surfaced counts in `app/(agent)/page.ts`; further UI polish deferred to Aspect design team.

### 4. Conversation Detail Lifecycle (Completed 2025-11-10)
- Detail + delete services wired through `lib/server/services/conversations.ts`.
- App Router proxies (`app/api/conversations/[conversationId]/route.ts`) live with unit tests.
- Sidebar + chat UI fetch history on selection and expose clear actions; ensure Playwright covers regression once UI polish stabilizes.

### 5. Chat Non-Streaming Endpoint (Completed 2025-11-10)
- App Router proxy already live; added `useSendChatMutation` to target it.
- Streaming flow now falls back to non-streaming mutation when SSE fails.
- Additional UI polish deferred; hook ready for broader reuse.

### 6. Billing Subscription Management (Completed 2025-11-10)
- Service helpers cover detail/start/update/cancel/usage flows.
- App Router proxies (`app/api/billing/tenants/*`) live with Vitest coverage.
- Provided TanStack hooks (`useTenantSubscription` + mutations) ready for future admin UI wiring.

### 7. Auth Lifecycle (Completed 2025-11-10)
- Added auth service helpers split by concern (sessions/email/passwords/service accounts/signup).
- App Router proxies mirror all remaining backend auth endpoints with unit coverage.
- Server actions wrap logout/password/email/register flows so UI can call them without touching cookies directly.

## Testing Expectations

- Unit: Vitest coverage for every new route, service helper, and hook.
- Integration: Expand Playwright journeys when UI paths change (login → manage subscription → chat → logout, etc.).
- Contract: When new endpoints surface in backend OpenAPI but generated client lacks methods, log in `docs/trackers/ISSUE_TRACKER.md` with reproduction steps.

## Coordination Notes

- Keep generated HeyAPI files untouched; surface generator omissions via ISSUE_TRACKER entries with the expected schema diff.
- Frontend and backend owners should sync weekly until parity is achieved to prevent drift between FastAPI routers and App Router proxies.
- Archive this milestone into `docs/trackers/complete/` once any final UI polish lands; parity is achieved.
