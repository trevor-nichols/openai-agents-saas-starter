# Frontend E2E Test Guide

_Last updated: November 19, 2025_

## 1. Environment
- Run `pnpm dev` (frontend) + `hatch run dev` (backend) locally or point Playwright to a deployed preview via `PLAYWRIGHT_BASE_URL`.
- Seed deterministic fixtures with the Starter CLI (`python -m starter_cli.app seed playground --answers-file ./seeds/playwright.yaml`). The answers file should describe every tenant/user listed in the table below so tests never depend on ad-hoc state.
- Required env vars (set in `.env.local.playwright` or CI secrets):
  - `PLAYWRIGHT_TENANT_ADMIN_EMAIL`, `PLAYWRIGHT_TENANT_ADMIN_PASSWORD`
- `PLAYWRIGHT_OPERATOR_EMAIL`, `PLAYWRIGHT_OPERATOR_PASSWORD`
- `PLAYWRIGHT_BASE_URL` (defaults to `http://localhost:3000`).

## 2. Deterministic Fixture Harness

Every Playwright flow in `app-regressions.spec.ts` assumes specific tenants, plans, and infrastructure toggles. Keep these seeded before running tests locally or in CI:

| Flow | Required Data / Infra | Seeding Notes |
| --- | --- | --- |
| Auth + chat handshake | Tenant `playwright-starter` with admin user + baseline conversations | Included in `seeds/playwright.yaml` as `tenant_admin` user; chat history populated via `starter_cli.app seed conversations`. |
| Self-serve signup + email verification | Invitation-free signup tenant plus disposable inbox token | Enable `ALLOW_PUBLIC_SIGNUP=true`, provision `signup_pending@example.com`, and rely on the `/api/v1/test-fixtures/email-verification-token` helper to mint deterministic tokens per test run. |
| Plan upgrade/downgrade + audit | Stripe plan codes `starter`, `scale`, plus mock invoices/events | Seed via `starter_cli.app seed billing --tenant playwright-starter --plans starter,scale`. Run backend with `ENABLE_BILLING=true` and Stripe stubs (`STRIPE_PRODUCT_PRICE_MAP="starter=price_test_starter,scale=price_test_scale"`). |
| Billing ledger & usage | Redis stream (`agents-redis`), usage rows via `/api/v1/billing/tenants/{id}/usage` | After seeding plans, call `python scripts/seed_usage.py --tenant playwright-starter --feature messages --quantity 42` (script lives under `scripts/`). Ensure `BILLING_EVENTS_REDIS_URL` matches the docker compose service. |
| Service-account issue/revoke | Operator tenant + Vault dev signer | Run `just vault-up` before tests. Seed operator `platform-ops@example.com` with `service_accounts:manage` scope and persist Vault token in `.env.local.playwright`. |
| Tenant settings update | Webhook echo endpoint + billing contacts | Include a webhook echo service (e.g., `http://localhost:8787/webhook-echo`) and seed default contacts so the spec can mutate + revert them. |
| Transcript export | Conversation with attachments + storage fake | Start backend with `USE_STORAGE_FAKE=true` and `STORAGE_FAKE_ROOT=tmp/playwright-storage`. Seed a conversation `transcript-seed` with at least three messages so export produces a file. |
| Conversations archive | Archived + active conversations across billing tiers | Seed one archived conversation per tenant and expose an API helper `scripts/seed_archive.py` that can reset the state between runs. |

Use `pnpm test:seed` to apply the canonical specification in `seeds/playwright.yaml`. Override the backend target with `PLAYWRIGHT_API_URL` (defaults to `http://localhost:8000`) or the spec file with `PLAYWRIGHT_SEED_FILE`. The command writes resolved identifiers to `tests/.fixtures.json` so Playwright helpers stay environment-agnostic.

- **Email verification tokens**: When `USE_TEST_FIXTURES=true`, the backend exposes `POST /api/v1/test-fixtures/email-verification-token` to mint disposable verification tokens without hitting Resend. The helper in `tests/utils/signup.ts` hits that endpoint so Flow 2 never depends on external email delivery. Make sure `ALLOW_PUBLIC_SIGNUP=true` (or `PLAYWRIGHT_ALLOW_PUBLIC_SIGNUP=true`) before running the spec; otherwise Playwright will skip it.

Recommended workflow for keeping fixtures fresh:
1. `pnpm test:seed` (or `PLAYWRIGHT_SEED_FILE=custom.yaml pnpm test:seed`)
2. `python scripts/seed_usage.py --tenant playwright-starter`
3. `python scripts/seed_archive.py --tenant playwright-starter`
4. `just vault-up` (if not already running)
5. `docker compose up -d agents-redis agents-postgres`

Each seed script writes its outputs (tenant IDs, auth tokens, webhook URLs) to `tests/.fixtures.json`. Playwright helpers read that file so specs never reach into `.env` directly.

## 3. Test Suite Layout
```
agent-next-15-frontend/tests/
├── auth-smoke.spec.ts          # existing login/chat/log-out happy path
├── app-regressions.spec.ts     # new scenarios (billing, service accounts, transcripts)
├── signup-email-verification.spec.ts  # Flow 2 coverage driven by deterministic email tokens
└── README.md                   # this guide

Common Playwright-only helpers live under `tests/utils/` (e.g., `signup.ts` for minting verification tokens, `testEnv.ts` for env resolution). Keep network or fixture plumbing there so specs remain focused on user journeys.
```

- `app-regressions.spec.ts` currently marks each scenario with `test.skip()` until data + mocks are wired. Replace each TODO block with the real flow once fixtures land.
- Keep specs idempotent: rely on seeded tenants or create ephemeral data via API helpers so CI remains deterministic.

## 4. Local Workflow
1. `cd agent-next-15-frontend`
2. `pnpm playwright test --config=playwright.config.ts --headed tests/auth-smoke.spec.ts`
3. Once fixtures exist, drop the `test.skip()` calls and run the new suites.
4. Use `PLAYWRIGHT_UPDATE_SNAPSHOTS=1 pnpm playwright test` whenever screenshot assertions are added.

## 5. Open Questions
- Do we want per-tenant cleanup hooks after billing plan mutations? (Consider using the CLI release command to reset catalog state.)
- Should transcript export downloads be stored under `tmp/playwright-downloads` for CI artifact uploads?
- Do we need a mocked Vault Transit server for CI, or is the existing `just vault-up` stack sufficient?

Document decisions here as the team finishes the scenarios.
