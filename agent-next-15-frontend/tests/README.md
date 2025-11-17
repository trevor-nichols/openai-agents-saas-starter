# Frontend E2E Test Guide

_Last updated: November 17, 2025_

## 1. Environment
- Run `pnpm dev` (frontend) + `hatch run dev` (backend) locally or point Playwright to a deployed preview via `PLAYWRIGHT_BASE_URL`.
- Seed a tenant + operator users using the Starter CLI (`python -m starter_cli.cli seed playground --answers-file ./seeds/playwright.yaml`). Ensure:
  - Tenant admin owns Starter plan with at least two plans available for upgrade/downgrade tests.
  - Platform operator has `service_accounts:manage` and Vault test signer credentials.
  - Conversations fixture exists for transcript export.
- Required env vars (set in `.env.local.playwright` or CI secrets):
  - `PLAYWRIGHT_TENANT_ADMIN_EMAIL`, `PLAYWRIGHT_TENANT_ADMIN_PASSWORD`
  - `PLAYWRIGHT_OPERATOR_EMAIL`, `PLAYWRIGHT_OPERATOR_PASSWORD`
  - `PLAYWRIGHT_BASE_URL` (defaults to `http://localhost:3000`).

## 2. Test Suite Layout
```
agent-next-15-frontend/tests/
├── auth-smoke.spec.ts          # existing login/chat/log-out happy path
├── app-regressions.spec.ts     # new scenarios (billing, service accounts, transcripts)
└── README.md                   # this guide
```

- `app-regressions.spec.ts` currently marks each scenario with `test.skip()` until data + mocks are wired. Replace each TODO block with the real flow once fixtures land.
- Keep specs idempotent: rely on seeded tenants or create ephemeral data via API helpers so CI remains deterministic.

## 3. Local Workflow
1. `cd agent-next-15-frontend`
2. `pnpm playwright test --config=playwright.config.ts --headed tests/auth-smoke.spec.ts`
3. Once fixtures exist, drop the `test.skip()` calls and run the new suites.
4. Use `PLAYWRIGHT_UPDATE_SNAPSHOTS=1 pnpm playwright test` whenever screenshot assertions are added.

## 4. Open Questions
- Do we want per-tenant cleanup hooks after billing plan mutations? (Consider using the CLI release command to reset catalog state.)
- Should transcript export downloads be stored under `tmp/playwright-downloads` for CI artifact uploads?
- Do we need a mocked Vault Transit server for CI, or is the existing `make vault-up` stack sufficient?

Document decisions here as the team finishes the scenarios.
