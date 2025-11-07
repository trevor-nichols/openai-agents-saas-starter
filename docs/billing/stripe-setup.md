# Stripe Setup (STRIPE-01)

This guide explains the minimum configuration required to turn on billing with Stripe in the `anything-agents` backend. The gateway, webhooks, and automation (STRIPE-02+) are still under active development, but the settings below must already be in place so the service can boot safely when `ENABLE_BILLING=true`.

## Prerequisites

1. **Durable storage** – Billing requires Postgres. Ensure `USE_IN_MEMORY_REPO=false` and provide a valid `DATABASE_URL`. The Docker helper `make dev-up` launches Postgres + Redis with the correct defaults sourced from `.env.compose` and your `.env.local`.
2. **Stripe account access** – You need permission to view the project in the Stripe Dashboard so you can create products/prices and view API/webhook keys. The backend talks directly to Stripe via the official Python SDK, so the secret key you provide must have customer/subscription/usage write scope (test mode keys are fine locally).
3. **Local env files** – Never commit secrets. Copy `.env.example` to `.env.local` and keep your Stripe credentials there (gitignored).

## Required environment variables

| Variable | Description | Where to find it |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | Server-side API key (starts with `sk_live_` or `sk_test_`). | Stripe Dashboard → Developers → API keys. |
| `STRIPE_WEBHOOK_SECRET` | Signing secret used to verify Stripe webhooks (starts with `whsec_`). | Stripe Dashboard → Developers → Webhooks (or `stripe listen --print-secret`). |
| `STRIPE_PRODUCT_PRICE_MAP` | Mapping of billing plan codes (e.g., `starter`, `pro`) to Stripe price IDs. Accepts JSON or comma-delimited `plan=price` pairs. | Create products/prices in Stripe, copy the resulting `price_...` identifiers. |

Add the variables plus the existing toggles to `.env.local`:

```env
USE_IN_MEMORY_REPO=false
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

## Stripe SDK usage

The FastAPI backend now calls Stripe directly from `app/infrastructure/stripe/client.py` using the official `stripe` Python package. Every billing API request (`/start`, `/update`, `/usage`) flows through this client, which:

- Injects `STRIPE_SECRET_KEY` for all calls.
- Looks up plan codes via `STRIPE_PRODUCT_PRICE_MAP` and provisions real customers/subscriptions.
- Records metered usage with Stripe’s Usage Records API, reusing any idempotency key you pass to `/usage` (or generating one when omitted).

Because of this, local environments must be able to reach `api.stripe.com`, and the provided key must have permission to manage customers, subscriptions, subscription items, and usage records in the relevant mode (test vs. live).
