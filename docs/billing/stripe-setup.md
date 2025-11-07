# Stripe Setup (STRIPE-01)

This guide explains the minimum configuration required to turn on billing with Stripe in the `anything-agents` backend. The gateway, webhooks, and automation (STRIPE-02+) are still under active development, but the settings below must already be in place so the service can boot safely when `ENABLE_BILLING=true`.

## Prerequisites

1. **Durable storage** – Billing requires Postgres. Provide a valid `DATABASE_URL`. The Docker helper `make dev-up` launches Postgres + Redis with the correct defaults sourced from `.env.compose` and your `.env.local`.
2. **Stripe account access** – You need permission to view the project in the Stripe Dashboard so you can create products/prices and view API/webhook keys. The backend talks directly to Stripe via the official Python SDK, so the secret key you provide must have customer/subscription/usage write scope (test mode keys are fine locally).
3. **Local env files** – Never commit secrets. Copy `.env.example` to `.env.local` and keep your Stripe credentials there (gitignored).

## Required environment variables

| Variable | Description | Where to find it |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | Server-side API key (starts with `sk_live_` or `sk_test_`). | Stripe Dashboard → Developers → API keys. |
| `STRIPE_WEBHOOK_SECRET` | Signing secret used to verify Stripe webhooks (starts with `whsec_`). | Stripe Dashboard → Developers → Webhooks (or `stripe listen --print-secret`). |
| `STRIPE_PRODUCT_PRICE_MAP` | Mapping of billing plan codes (e.g., `starter`, `pro`) to Stripe price IDs. Accepts JSON or comma-delimited `plan=price` pairs. | Create products/prices in Stripe, copy the resulting `price_...` identifiers. |

Optional but recommended for live dashboards:

| Variable | Description |
| --- | --- |
| `ENABLE_BILLING_STREAM` | Flip to `true` to expose the `/api/v1/billing/stream` SSE endpoint. Requires Redis. |
| `BILLING_EVENTS_REDIS_URL` | Redis connection string used for billing pub/sub. Defaults to `REDIS_URL` when omitted. |

Add the variables plus the existing toggles to `.env.local`:

```env
ENABLE_BILLING=true
STRIPE_SECRET_KEY=sk_test_your_project_key
STRIPE_WEBHOOK_SECRET=whsec_your_signing_secret
# JSON and comma-delimited formats are both accepted
STRIPE_PRODUCT_PRICE_MAP={"starter":"price_starter","pro":"price_pro"}
```

> ⚠️ **Secrets stay local** – Do not reuse the placeholder values from `.env.example`, do not commit real keys, and avoid exporting them in your shell history. The backend now fails fast if these values are missing while billing is enabled, so empty strings will not bypass the guard.

## Enabling billing end-to-end

1. Populate the variables above in `.env.local`.
2. Ensure Postgres is running (`make dev-up`) and run migrations (`make migrate`).
3. Flip `ENABLE_BILLING=true` and restart the FastAPI server (`hatch run serve` or your preferred process manager).
4. On startup the app verifies that Stripe settings are present before wiring the billing repository. Misconfigurations surface immediately with an error that lists the missing env vars.

## Automation helper

Prefer not to edit env files by hand? Run the STRIPE-02 setup script from the repo root:

```bash
pnpm install
pnpm stripe:setup
```

The assistant guides you through Stripe CLI login, optional `make dev-up`, Postgres connectivity checks, and then writes the required env vars while preserving any existing values. See `docs/scripts/stripe-setup.md` for detailed walkthroughs and sample output.

## Webhook configuration

1. **Local development** – Start the Stripe listener and forward events into the API:

   ```bash
   stripe listen --forward-to http://localhost:8000/webhooks/stripe
   ```

   Copy the printed `whsec_...` secret into `.env.local` (`STRIPE_WEBHOOK_SECRET`). The CLI can rotate secrets at any time, so re-run the helper or update the env file whenever you restart `stripe listen`.

2. **Hosted environments** – Create a webhook endpoint in the Stripe Dashboard that points to `https://<your-domain>/webhooks/stripe` and subscribe to the billing-focused events you care about (`customer.subscription.*`, `invoice.*`, `charge.*`). The backend now persists *every* event to the `stripe_events` table before attempting to process it.

3. **Observability** – Each event is labeled with its processing outcome (`received`, `processed`, `failed`) plus any error message. See `docs/billing/stripe-runbook.md` for replay guidance and operational checklists.

4. **Real-time streaming** – When `ENABLE_BILLING_STREAM=true`, the backend publishes normalized billing updates to Redis and serves them via `/api/v1/billing/stream` (SSE). The Next.js dashboard consumes this feed to render live status bubbles in the Billing Activity panel.

## Troubleshooting & Tests

- **Fixture-driven tests** – Run `make test-stripe` to replay fixture payloads through the webhook and streaming stack. This suite ensures event persistence and SSE broadcasting keep working without talking to live Stripe.
- **Replay CLI** – Use `make stripe-replay ARGS="list --status failed"` to inspect stored events and `make stripe-replay ARGS="replay --event-id evt_123"` to reprocess failures. Add `--dry-run` to inspect payloads.
- **Fixture linting** – `make lint-stripe-fixtures` loads every JSON file under `tests/fixtures/stripe/` to catch syntax errors before CI.
- **Redis unavailable** – The SSE endpoint returns `503` when `ENABLE_BILLING_STREAM=true` but no Redis URL is configured. Ensure `BILLING_EVENTS_REDIS_URL` (or `REDIS_URL`) points to a reachable instance.
- **CI flaky tests** – If the replay tests fail with `duplicate` responses, ensure fixtures have unique `id` values and run `make test-stripe` locally to reproduce.

## Stripe SDK usage

The FastAPI backend now calls Stripe directly from `app/infrastructure/stripe/client.py` using the official `stripe` Python package. Every billing API request (`/start`, `/update`, `/usage`) flows through this client, which:

- Injects `STRIPE_SECRET_KEY` for all calls.
- Looks up plan codes via `STRIPE_PRODUCT_PRICE_MAP` and provisions real customers/subscriptions.
- Records metered usage with Stripe’s Usage Records API, reusing any idempotency key you pass to `/usage` (or generating one when omitted).

Because of this, local environments must be able to reach `api.stripe.com`, and the provided key must have permission to manage customers, subscriptions, subscription items, and usage records in the relevant mode (test vs. live).
