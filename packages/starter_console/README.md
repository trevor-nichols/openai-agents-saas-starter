# Starter Console

Operator console for the OpenAI Agents SaaS starter stack. It is the single entrypoint for provisioning local or hosted environments, capturing secrets, running release workflows, and generating auditable artifacts and logs.

## What it does
- Bootstrap local infra (Postgres/Redis/Vault dev signer) and start/stop dev stacks.
- Guide setup via a milestone-aware wizard (interactive or headless) with audited outputs.
- Provision/validate third-party providers (Stripe, Resend) and seed billing data.
- Issue and rotate service-account keys/tokens; manage JWKS.
- Export backend OpenAPI for the frontend SDK, plus release/migration helpers.
- Tail and archive logs using the repo-wide logging layout.

## Prereqs
- Python 3.11+ (Hatch-managed env recommended)
- Docker Desktop or Docker Engine with the Compose plugin
- Node.js + pnpm only if you run frontend tasks or regenerate SDKs
- Stripe CLI only if you run `starter-console stripe setup`

## Install
- Recommended: `just python-bootstrap` (installs Python 3.11 + Hatch via `uv`), then `cd packages/starter_console && hatch env create`.
- Alternative: from repo root run `just dev-install` (editable installs for `starter_console`, `starter_contracts`, and `starter_providers`).

## Running the console
- Default TUI: `starter-console` (no args) launches the Textual home hub.
- CLI: `starter-console <command> [flags]` for headless execution.
- Non-interactive runs: `--non-interactive` plus `--answers-file`/`--var` for the setup wizard.
- Most commands support `--no-tui`, `--json`, or `--markdown` for CI-friendly output.

## Environment loading
- Default env files: `.env.compose`, `apps/api-service/.env`, `apps/api-service/.env.local`.
- Add files with `--env-file` (repeatable). Skip defaults with `--skip-env` or `STARTER_CONSOLE_SKIP_ENV=1`.
- Use `--quiet-env` to suppress load notices.
- Paths are resolved relative to the repo root, so you can run the console from any directory.
- `starter-console util run-with-env` merges explicit env files / `KEY=VALUE` overrides and then execs the command.

## Quick starts
- Demo bootstrap: `just setup-demo-lite` → `just api` → `just issue-demo-token`.
- Start/stop stack: `starter-console start dev --detached` then `starter-console stop`.
- Health report: `starter-console doctor --strict --json var/reports/operator-dashboard.json`.

## Command catalog (high-level)
- `setup menu|wizard`: setup hub + milestone wizard with hosting presets, automation toggles, and audit summaries.
- `infra deps|compose|vault`: verify prerequisites and manage Docker Compose + Vault dev signer.
- `start` / `stop`: start dev/backend/frontend with health checks; detach to run in the background.
- `home` / `doctor`: TUI hub and consolidated readiness probes (JSON/Markdown supported).
- `auth tokens|keys|jwks`: issue service-account tokens and rotate Ed25519 keys.
- `users ensure-dev|seed`: seed a dev user/tenant or a specific user.
- `secrets onboard`: onboarding for Vault, AWS Secrets Manager, Azure Key Vault, Infisical.
- `providers validate`: validate Stripe/Resend configuration (strict mode supported).
- `stripe`: provision catalog, capture webhook secrets, replay events.
- `release db`: run migrations + capture release summary (optionally Stripe checks).
- `usage sync-entitlements|export-report`: manage plan entitlements and export usage dashboards.
- `config dump-schema|write-inventory`: dump settings schema and env coverage inventory.
- `api export-openapi`: generate the OpenAPI schema used by the frontend SDK.
- `logs tail|archive`: tail structured logs or archive/prune dated log folders.
- `status subscriptions|incidents`: manage status API subscriptions and resend incidents.
- `util run-with-env`: merge env files + overrides then exec a command.

## Architecture (how it is built)
- **Entrypoint:** `starter_console.app` builds the CLI parser, resolves env overlays, and picks CLI vs TUI.
- **Commands:** `starter_console/commands/*` are thin adapters mapping CLI flags to services/workflows.
- **Services:** `starter_console/services/*` contain single-responsibility operations (infra, auth, config, stripe, usage).
- **Workflows:** `starter_console/workflows/*` orchestrate multi-step flows (setup, doctor, secrets, stripe, home).
- **Ports & presenters:** `starter_console/ports` defines console/presentation interfaces; `presenters` implement headless + Textual adapters.
- **UI layer:** `starter_console/ui/*` hosts the Textual TUI (panes, nav, context panel).
- **Core:** `starter_console/core/*` holds context, constants, exceptions, and status models.
- **Boundaries:** the console does not import FastAPI app modules directly; OpenAPI export runs the backend script instead.

## Artifacts & logs
- Reports live under `var/reports/` (setup summary, diff, usage exports, release summaries).
- Detached stack state is tracked in `var/run/stack.json` (used by `home`/`doctor`/`stop`).
- Logs follow `var/log/<YYYY-MM-DD>/<service>/{all.log,error.log}` with `var/log/current` pointing to the latest date.
- Textual debug logs go to `var/log/<date>/starter-console/textual.log` when `TEXTUAL_LOG` is set.

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

## Development & tests
- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- `cd packages/starter_console && hatch run test`

## Related docs
- `docs/ops/setup-wizard-presets.md`
- `docs/observability/README.md`
- `docs/security/secrets-providers.md`
- `docs/scripts/stripe-setup.md`
- `docs/ops/db-release-playbook.md`
