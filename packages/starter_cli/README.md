# Starter CLI

Operator tooling for the OpenAI Agents SaaS starter. It bootstraps local infra, seeds data, provisions secrets and Stripe, exports OpenAPI for the frontend SDK, and ships TUIs/health checks so you never need ad-hoc scripts.

## Prereqs & install
- Python environment with repo requirements; use `just dev-install` for editable installs of `starter_cli` + `starter_contracts`.
- Run from the repo root (paths resolve there even if you `cd packages/starter_cli`).
- Most commands auto-load `.env.compose`, `apps/api-service/.env.local`, `apps/api-service/.env`, `.env`; override with `--env-file`, or skip via `--skip-env`.

## Running the CLI
- Entry: `python -m starter_cli.app <command> [flags]`
- Console theming: `--console-theme`, `--console-width`, `--no-color`.
- Non-interactive: most flows support `--non-interactive` + `--answers-file` and honor env vars.

## Common workflows (fast path)
- Local lite bootstrap: `just setup-local-lite` (deps, wizard, dev user) then `just api` to start FastAPI; `just issue-demo-token` to mint a service token.
- Start services: `python -m starter_cli.app start dev|backend|frontend [--detached]`; stop detached with `python -m starter_cli.app stop`.
- Health dashboards: `python -m starter_cli.app home` (TUI) or `python -m starter_cli.app doctor --strict --json var/reports/operator-dashboard.json`.
- Seed users/tokens: `python -m starter_cli.app users ensure-dev` and `python -m starter_cli.app auth tokens issue-service-account --account demo-bot --scopes chat:write,conversations:read`.

## Command catalog (high level)
- Setup & onboarding: `setup wizard` (profile-aware, auto-infra/secrets/redis/migrations/geoip/stripe/dev-user), `setup menu` (status + TUI).
- Infra & lifecycle: `infra deps`, `start`, `stop`, `home`, `doctor`.
- Auth & users: `auth keys|tokens`, `users seed|ensure-dev`.
- Secrets: `secrets` onboarding for AWS Secrets Manager, Azure Key Vault, Infisical, Vault.
- Providers & billing: `providers` validation, `stripe` (dispatch fixtures, replay webhooks, capture webhook secret).
- Config & API: `config` (settings, inventories), `api export-openapi`.
- Usage & release: `usage` (entitlements/reporting), `release` (migration/seeding helpers), `logs`, `status`, `util run-with-env`.
Use `python -m starter_cli.app <command> --help` for subcommands/flags.

## OpenAPI export + frontend SDK regen
Paths are repo-root relative (do not prefix with `../`):

```bash
cd packages/starter_cli
python -m starter_cli.app api export-openapi \
  --output apps/api-service/.artifacts/openapi-fixtures.json \
  --enable-billing \
  --enable-test-fixtures

cd ../../apps/web-app
OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures
```

## Tips
- TUI vs headless: most commands pick TUI when a tty is present; pass `--no-tui` (when available) or use `--json/--markdown` outputs for automation.
- Detached stacks track state under `packages/starter_cli/var`; `doctor` and `home` read it to report running services.
- Wizard sections are declarative (`setup/schema.yaml`), so adding new setup prompts lives there instead of code.
