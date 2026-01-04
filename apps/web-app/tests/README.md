# Frontend Test Architecture

_Last updated: January 3, 2026_

## Testing Conventions

We keep test placement predictable so feature code and its checks travel together.

- **Route handlers:** Keep `route.test.ts` (or `route.test.tsx`) beside the matching `route.ts`.
- **Everything else:** Place tests in a sibling `__tests__/` directory next to the code under test.
- **E2E:** Playwright specs live in `tests/` and use fixtures/harnesses defined below.

Checks

- Run `pnpm lint:test-placement` (also included in `pnpm validate`) to fail on mis‑placed tests.

## 1. Harness + Env Contract

All Playwright configuration is validated by the harness in `tests/harness/`:

- `env.ts` — Zod-validated environment contract + derived flags.
- `fixtures.ts` — schema + helpers for `tests/.fixtures.json`.
- `seed.ts` — deterministic seeding orchestration (`pnpm test:seed`).
- `storageState.ts` — storage-state generation + freshness checks.
- `projects.ts` — CLI project selection parsing.

This keeps env logic in one place and makes E2E failures actionable and deterministic.

## 2. Environment

- Playwright will auto-start the Next.js app in CI (`pnpm build && pnpm start`) and reuse existing dev servers locally when available.
- Run the FastAPI backend (`hatch run dev`) for **real-backend** E2E flows, or point Playwright at a deployed preview via `PLAYWRIGHT_BASE_URL`.
- Seed deterministic fixtures with the Starter Console (`starter-console seed playground --answers-file ./seeds/playwright.yaml`) or `pnpm test:seed`.
- Required env vars (set in `.env.local.playwright` or CI secrets):
  - `PLAYWRIGHT_TENANT_ADMIN_EMAIL`, `PLAYWRIGHT_TENANT_ADMIN_PASSWORD`
  - `PLAYWRIGHT_OPERATOR_EMAIL`, `PLAYWRIGHT_OPERATOR_PASSWORD`
  - `PLAYWRIGHT_BASE_URL` (defaults to `http://localhost:3000`)
  - `PLAYWRIGHT_MOCK_BASE_URL` (defaults to `http://localhost:3001` for mocked UI runs)
  - `PLAYWRIGHT_API_URL` (defaults to `http://localhost:8000`)
  - `NEXT_PUBLIC_AGENT_API_MOCK=true` when running mock-mode UI outside Playwright (Playwright sets this automatically for the mock web server)
  - `PLAYWRIGHT_SKIP_WEB_SERVER=true` to skip auto-starting Next.js when pointing at remote URLs
  - `PLAYWRIGHT_SEED_ON_START=true` to auto-run `pnpm test:seed`
  - `PLAYWRIGHT_SKIP_SEED=true` to skip fixture validation/seed
  - `PLAYWRIGHT_REFRESH_STORAGE_STATE=true` to regenerate login storage state
  - `PLAYWRIGHT_SKIP_STORAGE_STATE=true` to skip storage-state generation

## 2.1 Playwright Projects
- **chromium-real**: real backend, seeded data, critical journeys (`*.spec.ts`).
- **chromium-mock**: fast UI regressions, `NEXT_PUBLIC_AGENT_API_MOCK=true`, runs `*.mock.spec.ts` (backend not required).
- Global setup caches authenticated storage states under `tests/.auth` (set `PLAYWRIGHT_REFRESH_STORAGE_STATE=true` to regenerate).

## 3. Deterministic Fixture Harness

Every Playwright flow in `regressions/` assumes specific tenants, plans, and infrastructure toggles. Keep these seeded before running tests locally or in CI:

| Flow | Required Data / Infra | Seeding Notes |
| --- | --- | --- |
| Auth + chat handshake | Tenant `playwright-starter` with admin user + baseline conversations | Included in `seeds/playwright.yaml` as `tenant_admin` user; chat history populated via `starter-console seed conversations`. |
| Self-serve signup + email verification | Invitation-free signup tenant plus disposable inbox token | Set `SIGNUP_ACCESS_POLICY=public`, provision `signup_pending@example.com`, and rely on the `/api/v1/test-fixtures/email-verification-token` helper to mint deterministic tokens per test run. |
| Plan upgrade/downgrade + audit | Stripe plan codes `starter`, `scale`, plus mock invoices/events | Seed via `starter-console seed billing --tenant playwright-starter --plans starter,scale`. Keep `STRIPE_PRODUCT_PRICE_MAP` populated so the optimistic UI + SSE assertions reflect real plans. |
| Billing ledger & usage | Redis stream (`agents-redis`), usage rows via `/api/v1/billing/tenants/{id}/usage` | The spec emits usage via authenticated `fetch('/api/billing/.../usage')`. Ensure Redis is running and the backend started with `ENABLE_BILLING_STREAM=true` so SSE updates land instantly. |
| Service-account issue/revoke | Operator tenant + Vault dev signer (optional when `VAULT_VERIFY_ENABLED=false`) | Run `just vault-up` before tests if Vault verification is enabled. When verification is off (default), browser issuance falls back to a dev-demo signature only when `USE_TEST_FIXTURES=true`. |
| Tenant settings update | Webhook echo endpoint + billing contacts | Include a webhook echo service (e.g., `http://localhost:8787/webhook-echo`) and seed default contacts so the spec can mutate + revert them without touching production webhooks. |
| Transcript export | Conversation with attachments + storage fake | Deterministic conversation `transcript-export-seed` must exist (handled by `pnpm test:seed`). Playwright needs permission to write downloads (default `.playwright-downloads/`). |
| Conversations archive | Archived + active conversations across billing tiers | Keep `USE_TEST_FIXTURES=true`; Flow 8 deletes the archived transcript and immediately replays it via `POST /api/v1/test-fixtures/apply`. |

Use `pnpm test:seed` to apply the canonical specification in `seeds/playwright.yaml`. Override the backend target with `PLAYWRIGHT_API_URL` (defaults to `http://localhost:8000`) or the spec file with `PLAYWRIGHT_SEED_FILE`. The command writes resolved identifiers to `tests/.fixtures.json` so Playwright helpers stay environment-agnostic.

- **Email verification tokens**: When `USE_TEST_FIXTURES=true`, the backend exposes `POST /api/v1/test-fixtures/email-verification-token` to mint disposable verification tokens without hitting Resend.
- **Archived conversation reset**: Flow deletes the archive seed then calls `POST /api/v1/test-fixtures/apply` to restore it. If `USE_TEST_FIXTURES` is disabled the replay step will fail.

## 4. Test Suite Layout
```
web-app/tests/
├── fixtures/
│   └── base.ts                  # Playwright fixtures (roles + env)
├── harness/
│   ├── env.ts                   # Zod env contract
│   ├── fixtures.ts              # Fixture schema + helpers
│   ├── projects.ts              # CLI project selector
│   ├── seed.ts                  # Seed runner + validation
│   └── storageState.ts          # Storage state utilities
├── global-setup.ts              # Playwright global setup (fixtures + storage state)
├── auth/
│   ├── auth-smoke.spec.ts       # login/chat/logout happy path
│   └── signup-email-verification.spec.ts  # self-serve signup flow
├── regressions/
│   ├── billing.spec.ts          # billing plan + usage flows
│   ├── chat-transcript-export.spec.ts # transcript export download flow
│   ├── conversation-archive.spec.ts   # archive delete/restore flow
│   ├── service-accounts.spec.ts # service account issuance + revoke
│   └── tenant-settings.spec.ts  # tenant controls + webhook updates
├── team/
│   └── team-org-smoke.spec.ts   # team membership + invites
├── workflows/
│   └── workflows.mock.spec.ts   # fast UI regressions (mock mode)
└── README.md                    # this guide
```

Common Playwright-only helpers live under `tests/utils/` (e.g., `signup.ts` for minting verification tokens, `appReady.ts` for waiting on dev compilation overlay). Keep network or fixture plumbing in the harness so specs remain focused on user journeys.

## 5. Local Workflow
1. `cd apps/web-app`
2. `pnpm test:seed` (real-backend flows)
3. `pnpm playwright test --project=chromium-real --headed tests/auth/auth-smoke.spec.ts`
4. `pnpm playwright test --project=chromium-mock --headed tests/workflows/workflows.mock.spec.ts`
5. Use `PLAYWRIGHT_UPDATE_SNAPSHOTS=1 pnpm playwright test` whenever screenshot assertions are added.

Note: `pnpm test:e2e` runs **both** projects; keep the backend running for the real-backend suite.

## 6. Open Questions
- Do we want per-tenant cleanup hooks after billing plan mutations? (Consider using the console release command to reset catalog state.)
- Should transcript export downloads be stored under `tmp/playwright-downloads` for CI artifact uploads?
- Do we need a mocked Vault Transit server for CI, or is `just vault-up` sufficient?

Document decisions here as the team finishes the scenarios.
