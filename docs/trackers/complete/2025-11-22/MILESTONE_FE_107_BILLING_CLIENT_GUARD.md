# Milestone: FE-107 Billing Client Regen Guard

**Status:** Complete  
**Milestone Owner:** *@codex*  
**Target Window:** 20–22 Nov 2025  

## Objective
Prevent billing-off environments from breaking the Next.js build while keeping billing fully wired when enabled. Do this by pinning the generated SDK to a billing-enabled OpenAPI artifact and gating all billing UX/API entry points behind a single runtime flag so operators/users need no extra steps.

## Success Criteria
1. The HeyAPI client always includes billing types/methods regardless of the operator’s local `ENABLE_BILLING` setting.
2. With `billingEnabled=false`, the UI hides billing navigation, pages short-circuit to 404/redirect, Next API routes return 404, and TanStack queries are disabled (no network calls fired).
3. Starter Console writes both `ENABLE_BILLING` (backend) and `NEXT_PUBLIC_ENABLE_BILLING` (frontend) during setup; operators do not hand-edit env files.
4. `pnpm lint` / `pnpm type-check` succeed in both billing-on and billing-off envs; no conditional imports are needed in app code.

## Workstreams & Tasks

### 1) Canonical OpenAPI Artifact
- [x] Export billing-enabled OpenAPI spec from FastAPI CI (e.g., `apps/api-service/.artifacts/openapi.json`) and reference it in `apps/web-app/openapi-ts.config.ts` instead of hitting the live dev server.
- [x] Document the source of truth in `web-app/README.md` and `docs/frontend/data-access.md`; warn contributors not to regenerate against a billing-off backend.
- [x] Add a lightweight CI guard that fails if the billing endpoints disappear from the artifact.

### 2) Runtime Feature Flag Plumbing
- [x] Add `billingEnabled` to `web-app/lib/config/features.ts` with default `false`; read `process.env.NEXT_PUBLIC_ENABLE_BILLING` and allow optional hydration from a features health endpoint if present.
- [x] Expose a minimal `/app/api/health/features` proxy (optional) that surfaces backend `ENABLE_BILLING`, keeping browser code env-light.

### 3) UI & Routing Guards
- [x] Hide billing links in the authenticated shell/nav when `!billingEnabled`.
- [x] Add guards to `app/(app)/(workspace)/billing` pages (or their layout) to `notFound()`/`redirect('/dashboard')` when disabled.
- [x] Mirror guards in `app/api/billing/**` route handlers to return 404 immediately when billing is off.

### 4) Data Layer Guards
- [x] Update billing TanStack hooks (`lib/queries/billing*.ts`) to pass `enabled: billingEnabled` and avoid issuing requests in billing-off mode.
- [x] Ensure client fetch helpers handle the 404 from guarded API routes cleanly (no user-facing error toasts when feature is off).
- [x] Keep server services importing the generated client directly; optional defensive import wrapper can emit a clear dev error if the SDK was regenerated incorrectly.

### 5) Starter Console & Env Parity
- [x] Update the console wizard section to write both `ENABLE_BILLING` (backend) and `NEXT_PUBLIC_ENABLE_BILLING` (frontend) together; default both to false unless the operator opts in.
- [x] Note the coupling in `docs/trackers/CONSOLE_MILESTONE.md` or the relevant console tracker if more guidance is needed.

### 6) Tests & DX
- [x] Add a minimal test asserting that with `NEXT_PUBLIC_ENABLE_BILLING=false`, the nav omits billing and hitting `/app/api/billing/plans` returns 404.
- [x] Add a unit test that billing queries are not enabled (query key not fired) when the flag is false.

### 7) Quality Gates
- [x] Run `pnpm lint` and `pnpm type-check` in `web-app`.
- [x] (If backend artifact generation changes) run `hatch run lint` / `hatch run typecheck` in `api-service` for safety. *(N/A this round — no backend changes.)*
- [x] Update `docs/trackers/ISSUE_TRACKER.md` status when milestone completes.

## Notes / Decisions
- Compile-time surface is always “billing-on”; runtime flag controls visibility/behavior. This avoids TypeScript breakage and keeps future billing expansions additive.
- No conditional imports in UI code; the flag lives in config and the routing/query layers do the gating.
- Operators do nothing beyond answering the CLI wizard; defaults are safe and feature-off yields a coherent experience (hidden nav + 404s).
