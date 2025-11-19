# Database Release Playbook

This runbook codifies the order-of-operations for shipping schema changes and billing plan seeding in the SaaS starter backend. Follow it before enabling or updating provider integrations (Stripe, Resend, etc.) so production stays predictable and auditable.

## Audience & Responsibilities
| Role | Responsibilities |
| --- | --- |
| Release captain | Owns the deploy window, runs the automation command, captures artifacts, and updates the tracker. |
| Billing/platform engineer | Confirms billing plans map to Stripe prices, monitors webhooks after release, and assists with rollback if needed. |
| SRE/on-call | Provides Postgres access, observes infra metrics, and enforces the checklist in CI/CD.

## Prerequisites
1. **Environment parity** – `.env.local` / deployment secrets contain the target `DATABASE_URL`, Redis URLs, and provider keys. Run `starter_cli config dump-schema` if you need to confirm coverage.
2. **Secrets** – `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the desired `STRIPE_PRODUCT_PRICE_MAP` entries are available (from prior runs or the upcoming release).
3. **Tooling** – Hatch environment created (`just bootstrap`), Docker/Compose available if you need local Postgres, and Stripe CLI installed+authenticated when using automation for Stripe provisioning.
4. **Access** – Operator can reach the deployment Postgres instance (psql/SSL tunnels). Verify credentials by running `psql $DATABASE_URL -c 'select 1'` prior to the window.

## Pre-flight Checklist
Run this list **before** touching production:
- [ ] Confirm git SHA/tag for the release candidate.
- [ ] Ensure no pending Alembic revisions on the source branch (`hatch run alembic -c anything-agents/alembic.ini heads`).
- [ ] Verify Postgres reachability (`psql $DATABASE_URL -c 'select version();'`).
- [ ] Run `just migrate` against a staging environment to smoke-test the revision.
- [ ] Validate provider inputs with `python -m starter_cli.app providers validate` so Stripe/Resend/OpenAI keys exist before billing is enabled.
- [ ] Confirm Stripe CLI authentication: `stripe whoami` should succeed (skip when using purely manual plan updates).

## Execution Order
### Option A – Automated (preferred)

Run the release helper whenever you promote a backend build:

```bash
python -m starter_cli.app release db \
  --summary-path var/reports/db-release-$(date -u +%Y%m%dT%H%M%SZ).json
```

Key flags:

- `--non-interactive` – fails instead of prompting; combine with `--plan starter=2000 --plan pro=9900` (or your catalog) to supply Stripe pricing and keep the run headless.
- `--skip-stripe` – skip provisioning when automation cannot hit Stripe (attach manual screenshots/artifacts).
- `--skip-db-checks` – skip the billing plan query (only when a separate evidence source exists).
- `--json` – also print the JSON summary to stdout.
- `--plan CODE=CENTS` – forwarded to the embedded Stripe setup flow; required for every plan during non-interactive runs.

The command executes the following steps:

1. Runs `just migrate` with the current `.env*` loads so FastAPI pods don't need `AUTO_RUN_MIGRATIONS`.
2. Captures the Alembic head via `hatch run alembic -c anything-agents/alembic.ini current`.
3. Invokes the Stripe provisioning flow unless `--skip-stripe` is set (same UX as `stripe setup`, including CLI validation unless `--non-interactive` is passed).
4. Queries `billing_plans` to ensure every required plan exists, is active, and has a Stripe price ID.
5. Emits `var/reports/db-release-*.json` containing timestamps, git SHA, Alembic revision, plan status, masked Stripe secrets, and the options used. Use `--summary-path` to override the location.

### Option B – Manual (until automation ships or when running in constrained environments)
1. **Migrations**
   ```bash
   just migrate
   hatch run alembic -c anything-agents/alembic.ini current
   ```
   Save the `alembic current` output in the release ticket.

2. **Stripe plan seeding**
   ```bash
   python -m starter_cli.app stripe setup \
     --non-interactive \
     --secret-key $STRIPE_SECRET_KEY \
     --webhook-secret $STRIPE_WEBHOOK_SECRET \
     --currency usd \
     --trial-days 14
   ```
   Provide `--plan starter=0` / `--plan pro=9900` overrides if pricing differs. Capture the JSON summary printed at the end.

3. **Post-run verification**
   ```bash
   psql $DATABASE_URL <<'SQL'
   select code, stripe_price_id, is_active
   from billing_plans
   order by code;
   SQL
   ```
   Confirm both `starter` and `pro` rows exist, are active, and have Stripe price IDs referenced in `.env.local`.

4. **Provider sanity** – `python -m starter_cli.app providers validate` and `python -m starter_cli.app status summary` (if available) should both return success.

## Evidence Capture
- Automation mode stores `var/reports/db-release-*.json`. Upload the file to your release record/PR and attach console logs.
- Manual mode: attach the following artifacts to the release or change ticket:
  - `alembic current` output showing the target revision.
  - `billing_plans` SQL result (redact price IDs if needed).
  - Stripe CLI summary JSON printed by the setup command.
  - Any screenshots/logs proving provider validation succeeded.

## Rollback / Recovery
1. **Schema rollback** – Use Alembic to revert once: `hatch run alembic -c anything-agents/alembic.ini downgrade -1`. Coordinate with engineering to confirm whether data migrations require manual cleanup.
2. **Stripe rollback** – Archive newly created prices/products in the Stripe dashboard or via CLI. Update `.env.local` to point back to known-good `price_…` IDs.
3. **Re-run release** – After fixing issues, repeat the Execution Order (automation or manual) and attach fresh artifacts.

## Frequently Asked Questions
**Q: Can I rely on FastAPI to run migrations automatically?**
No. `AUTO_RUN_MIGRATIONS` remains `false` outside local dev, so pods refuse to auto-upgrade schema. Always run this playbook.

**Q: What if Stripe automation is forbidden in CI?**
Use the `--skip-stripe` flag (once the release command lands) and follow the manual plan seeding steps. Attach the manual evidence to the release summary.

**Q: How do I know which database the CLI targets?**
`just migrate` loads env files via `scripts/run_with_env.py`, respecting `.env.compose` + `.env.local`. Confirm `DATABASE_URL` before running the commands, especially when using remote Postgres.

**Q: When should this runbook be updated?**
Whenever a new migration workflow, plan catalog change, or CLI flag lands. Log the update in `docs/trackers/MILESTONE_DB_RELEASE_AUTOMATION.md` and reference the change in release notes.
