# Stripe Developer Setup Script (STRIPE-02)

The `scripts/stripe/setup.ts` helper guides developers through the minimum tasks required before enabling billing. It does **not** talk to Stripe APIs yet—it orchestrates local tooling (Stripe CLI, Docker/Postgres, env files) so the STRIPE-01 startup guard can succeed without manual file edits.

## Prerequisites

- Node.js 18+ with [pnpm](https://pnpm.io/installation) (Corepack-enabled on macOS/Linux by default).
- Stripe CLI installed locally (`stripe --version` should work). The script can launch the guided auth page and run `stripe login --interactive` for you.
- Docker + `make` if you want it to bootstrap the local Postgres stack (`make dev-up`).
- A Stripe account with permission to create API keys, webhook endpoints, and price IDs.

## Running the script

```bash
pnpm install         # one-time, installs tsx/types
pnpm stripe:setup
```

The assistant walks through three phases:

1. **Stripe CLI check** – Verifies install + auth. If auth is missing it can
   - open <https://dashboard.stripe.com/stripe-cli/auth> in your browser, and
   - launch `stripe login --interactive` directly inside the terminal.
2. **Postgres helper** – Optionally runs `make dev-up` (Docker Compose) and can attempt a `psql` connection against `DATABASE_URL` (parsed from `.env.local`, `.env`, or `.env.compose`).
3. **Env writer** – Prompts for `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and plan-to-price mappings. Existing values are detected; you can keep them or overwrite. Results are written to `.env.local` and `ENABLE_BILLING` is flipped to `true` so the STRIPE-01 guard can succeed.

Sample (truncated) output:

```
[2025-11-07T21:12:52.483Z] [INFO] Welcome to the Stripe setup assistant.
[2025-11-07T21:12:52.732Z] [SUCCESS] Stripe CLI detected (stripe version 1.18.1).
[2025-11-07T21:12:56.410Z] [INFO] Start/refresh the local Postgres stack via `make dev-up`? (Y/n)
...
[2025-11-07T21:13:47.022Z] [SUCCESS] Stripe configuration saved to .env.local
```

If a step fails (missing CLI, Docker unavailable, `psql` not installed) the script will warn and continue so you can resolve the issue manually.

## Relationship to STRIPE-01

The FastAPI startup guard (STRIPE-01) now refuses to boot with `ENABLE_BILLING=true` unless `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRODUCT_PRICE_MAP` are populated. Running `pnpm stripe:setup` ensures those values land in `.env.local` and keeps existing values unless you explicitly overwrite them.

## Next steps

- **Webhook + gateway work (STRIPE-03/04/05)** will reuse the env values captured here.
- The script currently avoids real Stripe API calls; once STRIPE-03 lands we can extend it to verify price IDs via the official API if desired.
- Contributions welcome—see `scripts/stripe/setup.ts` for implementation details.
