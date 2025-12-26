# Starter Console

Operator tooling for the OpenAI Agents SaaS starter. It bootstraps local infra, seeds data, provisions secrets and Stripe, exports OpenAPI for the frontend SDK, and ships TUIs/health checks so you never need ad-hoc scripts.

## Prereqs & install
- Recommended: run `just python-bootstrap` (installs Python 3.11 + Hatch via `uv`), then `cd packages/starter_console && hatch env create`.
- Alternative: from repo root run `just dev-install` (editable installs for `starter_console` + `starter_contracts` + `starter_providers`).
- Docker Desktop or Docker Engine with the Compose plugin (`docker compose`).
- Run commands from the repo root (paths are repo-root relative even if you `cd packages/starter_console`).
- Env loading: defaults to `.env.compose`, `apps/api-service/.env.local`, `apps/api-service/.env`, `.env`. Override with `--env-file`; `--skip-env` skips defaults but still loads explicit `--env-file` values. Quiet logging with `--quiet-env`.

## Running the Console
- Entry: `starter-console <command> [flags]`
- Headless: most flows support `--non-interactive` plus `--answers-file`/`--var`; TUIs can be forced off with `--no-tui` where supported.

## Architecture notes (Console + TUI)
- **Presentation-only TUI:** Textual panes call services/workflows, not console command handlers. Command modules stay thin and map args → service configs.
- **Env overlay semantics:** `CLIContext.load_environment()` applies a tracked overlay from env files. The TUI Context panel can clear that overlay (Skip env load) and reapply it (Reload Env) without restarting the TUI. This prevents stale `.env` values from leaking into later runs.
- **Nav groups:** The command palette includes category entries (Overview, Onboarding, Operations, etc.) plus individual panes.
- **Service boundaries:** services are grouped under `starter_console/services/{api,auth,config,infra,secrets,stripe,usage}` to keep infra/ops concerns separate from auth, config inventory, and API export.
- **Backend-owned OpenAPI export:** the console invokes `apps/api-service/scripts/export_openapi.py` instead of importing backend modules directly, preserving the console ↔ backend boundary.

## Quick starts
- Demo bootstrap: `just setup-demo-lite` (deps, wizard, dev user) then `just api`; mint a token with `just issue-demo-token`.
- Start/stop services: `starter-console start dev|backend|frontend [--detached]`; stop detached stacks with `starter-console stop`.
- Health: `starter-console home` (TUI) or `starter-console doctor --strict --json var/reports/operator-dashboard.json`.
- Seed users/tokens: `starter-console users ensure-dev` and `starter-console auth tokens issue-service-account --account demo-bot --scopes chat:write,conversations:read`.

## Command catalog (what each one does)
- `setup menu|wizard`: Setup hub + milestone-aware wizard with hosting presets (`local_docker`, `cloud_managed`, `enterprise_custom`) and automation toggles for infra, secrets, Stripe, migrations, Redis, GeoIP, dev user; supports headless runs, schema-driven prompts, JSON/Markdown summaries, and answer export. For `--profile demo`, the wizard can manage Docker Postgres end-to-end (writes `POSTGRES_*` and derives `DATABASE_URL`) or accept an external `DATABASE_URL` and set `STARTER_LOCAL_DATABASE_MODE=external` so `infra compose up` starts Redis without launching Postgres.
- `infra deps|compose|vault`: Check local prerequisites; run Just recipes for the docker compose dev stack and Vault dev signer (up/down/logs/verify).
- `start` / `stop`: Start dev/backend/frontend with health checks; detached mode tracks PIDs/logs and can auto-run infra; stop clears state and optionally runs compose down.
- `home`: TUI/summary showing stack status, detached processes, and shortcuts.
- `doctor`: Consolidated readiness probes (api, db, redis, billing, ports, migrations, secrets, storage, frontend, vault, stack state); outputs summary/JSON/Markdown; strict mode treats warnings as errors.
- `auth tokens|keys|jwks`: Issue service-account refresh tokens (scopes/tenant/lifetime/output formats/base URL); rotate Ed25519 keys via Vault/backing store; print JWKS.
- `users ensure-dev|seed`: Create or rotate the default dev user/tenant or seed a specific user with optional rotation, locking, and prompted/generated passwords.
- `secrets onboard`: Guided or headless onboarding for Vault dev/AWS Secrets Manager/Azure Key Vault/Infisical; supports answers files, `--var` overrides, skip-automation, and logs verification artifacts.
- `providers validate`: Validate Stripe/Resend config; Stripe violations become fatal when billing is enabled.
- `stripe`: Provision plans/prices, capture webhook secret (via Stripe CLI), replay webhooks, and seed catalog with non-interactive overrides.
- `release db`: Run migrations via `just migrate`, capture Alembic revision, optionally run Stripe setup and billing plan verification, write JSON summary (optionally print).
- `usage sync-entitlements|export-report`: Upsert/prune usage entitlements from artifact; export tenant/plan/feature usage dashboard as JSON/CSV with filters and thresholds.
- `config dump-schema|write-inventory`: List all backend env vars with types/defaults/wizard coverage (table/JSON) or write Markdown inventory (`docs/trackers/CONSOLE_ENV_INVENTORY.md` by default).
- `api export-openapi`: Generate FastAPI OpenAPI schema with optional billing/test-fixtures/title/version overrides (repo-root relative output path).
- `logs tail|archive`: Tail api/frontend/collector/postgres/redis/all logs (errors-only, lines, follow) or archive/prune dated log dirs under `var/log`.
- `status subscriptions|incidents`: List/revoke subscriptions and resend incidents against the status API (needs `STATUS_API_TOKEN`).
- `util run-with-env`: Merge env files/KEY=VAL pairs then exec a command (use `--` to separate args).

## OpenAPI export + frontend SDK regen
Paths are repo-root relative (do not prefix with `../`):

```bash
cd packages/starter_console
starter-console api export-openapi \
  --output apps/api-service/.artifacts/openapi-fixtures.json \
  --enable-billing \
  --enable-test-fixtures

cd ../../apps/web-app
OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures
```

## Tips
- TUIs auto-enable when a tty is present; prefer `--json`/`--markdown` or `--no-tui` in CI.
- Detached stacks track state under `packages/starter_console/var`; `home` and `doctor` read it.
- Wizard prompts are declared in `setup/schema.yaml`; extend there to add new setup items.
- Each wizard run writes a redacted snapshot + diff under `var/reports/setup-snapshot.json` and `var/reports/setup-diff.md` for auditability.
- Hosting preset guidance lives in `docs/ops/setup-wizard-presets.md`.

## Console logging overrides (runbook)
The setup wizard writes backend `LOGGING_*` values into `apps/api-service/.env.local`. The Starter Console uses those values as defaults, but you can override console-only logging without touching the backend by setting `CONSOLE_LOGGING_*` env vars in any loaded env file (or inline on the command).

Common overrides:
- `CONSOLE_LOGGING_SINKS` (defaults to `file` for console runs)
- `CONSOLE_LOG_ROOT` (defaults to `LOG_ROOT` when set)
- `CONSOLE_LOGGING_FILE_PATH`, `CONSOLE_LOGGING_FILE_MAX_MB`, `CONSOLE_LOGGING_FILE_BACKUPS`
- `CONSOLE_LOGGING_OTLP_ENDPOINT`, `CONSOLE_LOGGING_OTLP_HEADERS`
- `CONSOLE_LOGGING_DATADOG_API_KEY`, `CONSOLE_LOGGING_DATADOG_SITE`

Example (console-only OTLP without changing backend logs):
```bash
CONSOLE_LOGGING_SINKS=otlp \
CONSOLE_LOGGING_OTLP_ENDPOINT=http://otel-collector:4318/v1/logs \
starter-console setup wizard
```
