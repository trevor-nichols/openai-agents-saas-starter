# Stripe Setup (STRIPE-01)

This guide explains the minimum configuration required to turn on billing with Stripe in the `api-service` backend. The STRIPE-02 helper now provisions the default plans (Starter + Pro) for you, but the environment variables below still need to be present so the service can boot safely when `ENABLE_BILLING=true`.

## Prerequisites

1. **Durable storage** – Billing requires Postgres. Provide a valid `DATABASE_URL`. The Docker helper `just dev-up` launches Postgres + Redis with the correct defaults sourced from `.env.compose` and your `apps/api-service/.env.local`.
2. **Stripe account access** – You need permission to view the project in the Stripe Dashboard so you can create products/prices and view API/webhook keys. The backend talks directly to Stripe via the official Python SDK, so the secret key you provide must have customer/subscription/usage write scope (test mode keys are fine locally).
3. **Local env files** – Never commit secrets. Copy `apps/api-service/.env.example` to `apps/api-service/.env.local` and keep your Stripe credentials there (gitignored).

## Required environment variables

| Variable | Description | Where to find it |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | Server-side API key (starts with `sk_live_` or `sk_test_`). | Stripe Dashboard → Developers → API keys. |
| `STRIPE_WEBHOOK_SECRET` | Signing secret used to verify Stripe webhooks (starts with `whsec_`). | Stripe Dashboard → Developers → Webhooks (or `stripe listen --print-secret`). |
| `STRIPE_PRODUCT_PRICE_MAP` | Mapping of billing plan codes (e.g., `starter`, `pro`) to Stripe price IDs. Accepts JSON or comma-delimited `plan=price` pairs. | **Recommended:** run `pnpm stripe:setup` and let it create the plans/prices automatically. Manual override: create the products/prices in Stripe and paste the `price_...` identifiers here. |

Optional but recommended for live dashboards:

| Variable | Description |
| --- | --- |
| `ENABLE_BILLING_STREAM` | Flip to `true` to expose the `/api/v1/billing/stream` SSE endpoint. Requires Redis. |
| `BILLING_EVENTS_REDIS_URL` | Redis connection string used for billing pub/sub. Defaults to `REDIS_URL` when omitted. |

Add the variables plus the existing toggles to `apps/api-service/.env.local` (the setup script writes this JSON automatically):

```env
ENABLE_BILLING=true
STRIPE_SECRET_KEY=sk_test_your_project_key
STRIPE_WEBHOOK_SECRET=whsec_your_signing_secret
# JSON and comma-delimited formats are both accepted
STRIPE_PRODUCT_PRICE_MAP={"starter":"price_123","pro":"price_456"}
```

> ⚠️ **Secrets stay local** – Do not reuse the placeholder values from `apps/api-service/.env.example`, do not commit real keys, and avoid exporting them in your shell history. The backend now fails fast if these values are missing while billing is enabled, so empty strings will not bypass the guard.

## Startup validation & troubleshooting

Before deploying, run `just validate-providers` (or `cd packages/starter_console && starter-console providers validate --strict`)
to confirm Stripe env vars are present—the CLI shares the same validator FastAPI uses during startup and
will exit non-zero whenever billing is enabled but a Stripe variable is missing (dev/staging/prod alike).

| Symptom / Log snippet | What it means | Fix |
| --- | --- | --- |
| `RuntimeError: ENABLE_BILLING=true requires Stripe configuration. Set ...` | Billing is enabled but one or more required env vars (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRODUCT_PRICE_MAP`) is missing or empty. | Populate the missing variables in `apps/api-service/.env.local` and restart the server. |
| `ValueError: Invalid STRIPE_PRODUCT_PRICE_MAP entry...` | The price map string could not be parsed (bad JSON or malformed `plan=price` pairs). | Provide valid JSON (recommended) or comma-delimited `plan=price` entries with no stray spaces. |
| `INFO ... Stripe billing configuration validated; 2 plan(s) mapped.` (with `stripe_config=` payload) | Startup verification succeeded. Secrets are masked and the log lists the plan codes plus whether the Redis billing stream is enabled. | No action required. If the stream is expected but the log shows `"billing_stream_backend": "disabled"`, set `ENABLE_BILLING_STREAM=true` and configure the Redis URL. |

When validation passes you will see a structured log similar to:

```
INFO saas_starter_db.main Stripe billing configuration validated; 2 plan(s) mapped. stripe_config={'stripe_secret_key': 'sk**********1234', 'stripe_webhook_secret': 'wh**********abcd', 'plans_configured': ['pro', 'starter'], 'plan_count': 2, 'billing_stream_enabled': False, 'billing_stream_backend': 'disabled'}
```

Use the masked prefixes/suffixes to confirm you copied the right keys without exposing them in plaintext logs.

## Enabling billing end-to-end

1. Populate the variables above in `apps/api-service/.env.local`.
2. Ensure Postgres is running (`just dev-up`) and run migrations (`just migrate`).
3. Flip `ENABLE_BILLING=true` and restart the FastAPI server (`cd apps/api-service && hatch run serve` or your preferred process manager).
4. On startup the app verifies that Stripe settings are present before wiring the billing repository. Misconfigurations surface immediately with an error that lists the missing env vars.

## Automation helper

Prefer not to edit env files by hand? Run the STRIPE-02 Python setup script from the repo root:

```bash
pnpm stripe:setup
```

The assistant guides you through Stripe CLI login, optional `just dev-up`, Postgres connectivity checks, and then asks for the monthly price of the Starter and Pro plans. It automatically creates/reuses the Stripe products/prices (7-day trial included) and writes the resulting env vars while preserving any existing values. See `docs/scripts/stripe-setup.md` for detailed walkthroughs and sample output.

## Webhook configuration

1. **Local development** – Start the Stripe listener and forward events into the API:

   ```bash
   stripe listen --forward-to http://localhost:8000/webhooks/stripe
   ```

   Copy the printed `whsec_...` secret into `apps/api-service/.env.local` (`STRIPE_WEBHOOK_SECRET`). The CLI can rotate secrets at any time, so re-run the helper or update the env file whenever you restart `stripe listen`.

2. **Hosted environments** – Create a webhook endpoint in the Stripe Dashboard that points to `https://<your-domain>/webhooks/stripe` and subscribe to the billing-focused events you care about (`customer.subscription.*`, `invoice.*`, `charge.*`). The backend now persists *every* event to the `stripe_events` table before attempting to process it.

3. **Observability** – Each event is labeled with its processing outcome (`received`, `processed`, `failed`) plus any error message. See `docs/billing/stripe-runbook.md` for replay guidance and operational checklists.

4. **Real-time streaming** – When `ENABLE_BILLING_STREAM=true`, the backend publishes normalized billing updates to Redis and serves them via `/api/v1/billing/stream` (SSE). The Next.js dashboard consumes this feed to render live status bubbles in the Billing Activity panel.

## Troubleshooting & Tests

- **Fixture-driven tests** – Run `just test-stripe` to replay fixture payloads through the webhook and streaming stack. This suite ensures event persistence and SSE broadcasting keep working without talking to live Stripe.
- **Replay CLI** – Use `just stripe-replay args="list --handler billing_sync --status failed"` to inspect stored dispatch rows and `just stripe-replay args="replay --dispatch-id <uuid>"` to reprocess failures without re-sending webhooks.
- **Fixture linting** – `just lint-stripe-fixtures` loads every JSON file under `tests/fixtures/stripe/` to catch syntax errors before CI.
- **Redis unavailable** – The SSE endpoint returns `503` when `ENABLE_BILLING_STREAM=true` but no Redis URL is configured. Ensure `BILLING_EVENTS_REDIS_URL` (or `REDIS_URL`) points to a reachable instance.
- **CI flaky tests** – If the replay tests fail with `duplicate` responses, ensure fixtures have unique `id` values and run `just test-stripe` locally to reproduce.

## Stripe SDK usage

The FastAPI backend now calls Stripe directly from `app/infrastructure/stripe/client.py` using the official `stripe` Python package. Every billing API request (`/start`, `/update`, `/usage`) flows through this client, which:

- Injects `STRIPE_SECRET_KEY` for all calls.
- Looks up plan codes via `STRIPE_PRODUCT_PRICE_MAP` and provisions real customers/subscriptions.
- Records metered usage with Stripe’s Usage Records API, reusing any idempotency key you pass to `/usage` (or generating one when omitted).

Because of this, local environments must be able to reach `api.stripe.com`, and the provided key must have permission to manage customers, subscriptions, subscription items, and usage records in the relevant mode (test vs. live).
