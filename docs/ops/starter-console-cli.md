# Starter Console — Command Reference

This project exposes two main ways to run automation:

1. **Project tasks** via **Just** + **Hatch** (`just …`, `hatch run …`)
2. A curated operator **CLI** via **Starter Console** (`starter-console …`)

> Entry point: `starter-console` (or `python -m starter_console.app`). Running without arguments launches the TUI home hub.

Global flags (available on all commands):
- `--env-file <PATH>` (repeatable)
- `--skip-env`
- `--quiet-env`

Note: Many flags are command-specific (for example, `--no-tui`, `--json`, `--markdown`).
Tip: `starter-console --help` and `starter-console <command> --help` are the authoritative sources for flags and subcommands.

---

## Common workflows

**Run the interactive setup wizard**
```bash
# Guided setup for secrets, providers, and infra
starter-console setup wizard --profile demo
```

**Start the development stack**
```bash
# Starts backend, frontend, and infra services
starter-console start dev
```

**Stream logs for all services**
```bash
starter-console logs tail --follow
```

**Local dev (typical)**

```bash
just python-bootstrap
just dev-install
starter-console setup wizard
starter-console start dev
starter-console doctor
starter-console logs tail
```

**Run quality gates (console only)**

```bash
just cli-lint
just cli-typecheck
just cli-test
```

**Infra only (compose)**

```bash
starter-console infra deps
starter-console infra compose up
starter-console infra compose logs
starter-console infra compose down
```

---

## Project tasks (Just + Hatch)

Use `just …` when you want a short alias. Use `hatch run …` when you want the underlying task directly (from `packages/starter_console`).

| Command                         | What it does                             | Notes                                                        |
| ------------------------------- | ---------------------------------------- | ------------------------------------------------------------ |
| `just python-bootstrap`         | Installs Python 3.11 + Hatch (via uv).   | Repo root. Recommended first step.                           |
| `just dev-install`              | Installs console + shared deps editable. | Repo root. Preferred local setup.                            |
| `just cli-lint`                 | Runs linting (`ruff check src`).         | Repo root. Delegates to `packages/starter_console`.          |
| `just cli-typecheck`            | Runs type checks (`pyright` + `mypy`).   | Repo root. Delegates to `packages/starter_console`.          |
| `just cli-test`                 | Runs the test suite (`pytest`).          | Repo root. Delegates to `packages/starter_console`.          |
| `cd packages/starter_console && just bootstrap` | Creates/refreshes the console Hatch env. | Package-scoped helper.                                       |
| `cd packages/starter_console && just lint`      | Runs `ruff check src`.                   | Package-scoped helper (same as `hatch run lint`).            |
| `cd packages/starter_console && just typecheck` | Runs `pyright` and `mypy`.               | Package-scoped helper (same as `hatch run typecheck`).       |
| `cd packages/starter_console && just test`      | Runs tests via `pytest`.                 | Package-scoped helper (same as `hatch run test`).            |
| `hatch run lint`                | Runs `ruff check src`.                   | Run inside `packages/starter_console`.                       |
| `hatch run format`              | Formats code (`ruff format src`).        | Run inside `packages/starter_console`; writes changes.       |
| `hatch run typecheck`           | Runs `pyright` and `mypy`.               | Run inside `packages/starter_console`.                       |
| `hatch run test`                | Runs tests via `pytest`.                 | Run inside `packages/starter_console`.                       |
| `hatch run pyright`             | Runs `pyright`.                          | Run inside `packages/starter_console`.                       |

---

## Starter Console CLI

The CLI is organized into command groups (setup, infra, stripe, auth, etc.). Commands below list the implementation file so developers can jump to the source quickly.

Legend:

* ⚠️ = mutates state, writes secrets, or deletes data

---

## Setup & configuration

| Command                                           | What it does                                      | Implementation                            | Notes                                                                    |
| ------------------------------------------------- | ------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ |
| `starter-console setup wizard`                    | Runs an interactive setup wizard.                 | `packages/starter_console/src/starter_console/commands/setup.py`   | Supports headless usage via flags like `--non-interactive`, `--profile`. |
| `starter-console setup menu` (alias: `dashboard`) | Opens the setup hub dashboard.                    | `packages/starter_console/src/starter_console/commands/setup.py`   | Primary entry for setup workflows.                                       |
| `starter-console secrets onboard`                 | Guided setup for secrets/signing providers.       | `packages/starter_console/src/starter_console/commands/secrets.py` | ⚠️ Writes/records secrets or secret-provider config.                     |
| `starter-console config dump-schema`              | Lists backend environment variables and defaults. | `packages/starter_console/src/starter_console/commands/config.py`  | Use to understand required env surface area.                             |
| `starter-console config write-inventory`          | Generates the environment inventory Markdown doc. | `packages/starter_console/src/starter_console/commands/config.py`  | ⚠️ Writes files (doc output).                                            |
| `starter-console users ensure-dev`                | Ensures a default developer account exists.       | `packages/starter_console/src/starter_console/commands/users.py`   | ⚠️ Creates/updates data.                                                 |
| `starter-console users seed`                      | Seeds a specific user into a tenant.              | `packages/starter_console/src/starter_console/commands/users.py`   | ⚠️ Creates/updates data.                                                 |
| `starter-console sso setup`                       | Seeds an OIDC SSO provider config.                | `packages/starter_console/src/starter_console/commands/sso.py`     | ⚠️ Writes SSO config/state.                                              |

---

## Infrastructure & operations

| Command                                                               | What it does                                        | Implementation                              | Notes                                       |
| --------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| `starter-console start [dev\|backend\|frontend]`                      | Starts local services (API, frontend, infra).       | `packages/starter_console/src/starter_console/commands/start.py`     | Mode selects which components to start.     |
| `starter-console stop`                                                | Stops services started by `start`.                  | `packages/starter_console/src/starter_console/commands/stop.py`      | Clean shutdown helper.                      |
| `starter-console home`                                                | Interactive home hub showing stack status.          | `packages/starter_console/src/starter_console/commands/home.py`      | Home view for local status.                 |
| `starter-console doctor`                                              | Runs readiness checks for the deployment profile.   | `packages/starter_console/src/starter_console/commands/doctor.py`    | Use to validate local/profile health.       |
| `starter-console logs tail`                                           | Tails logs for selected services.                   | `packages/starter_console/src/starter_console/commands/logs.py`      | Useful during local development.            |
| `starter-console logs archive`                                        | Archives and prunes dated log directories.          | `packages/starter_console/src/starter_console/commands/logs.py`      | ⚠️ Deletes/prunes logs.                     |
| `starter-console infra compose [up\|down\|logs\|ps]`                  | Wrapper for Docker Compose actions via Just.        | `packages/starter_console/src/starter_console/commands/infra.py`     | Uses Just targets behind the scenes.        |
| `starter-console infra vault [up\|down\|logs\|verify]`                | Wrapper for Vault dev signer actions via Just.      | `packages/starter_console/src/starter_console/commands/infra.py`     | Useful for local signing/secrets flows.     |
| `starter-console infra deps`                                          | Checks for local dependencies (Docker, Node, etc.). | `packages/starter_console/src/starter_console/commands/infra.py`     | Preflight your machine setup.               |
| `starter-console infra terraform export --provider <aws\|azure\|gcp>` | Generates a `tfvars` file for a hosting provider.   | `packages/starter_console/src/starter_console/commands/infra.py`     | ⚠️ Writes files (tfvars output).            |
| `starter-console providers validate`                                  | Validates configuration for third-party providers.  | `packages/starter_console/src/starter_console/commands/providers.py` | Use before deploying/integrating providers. |

---

## Billing (Stripe)

| Command                                               | What it does                                           | Implementation                           | Notes                                         |
| ----------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------- | --------------------------------------------- |
| `starter-console stripe setup`                        | Interactive onboarding for billing assets and secrets. | `packages/starter_console/src/starter_console/commands/stripe.py` | ⚠️ Writes/records billing config and secrets. |
| `starter-console stripe webhook-secret`               | Captures Stripe webhook signing secret via Stripe CLI. | `packages/starter_console/src/starter_console/commands/stripe.py` | ⚠️ Writes secret material.                    |
| `starter-console stripe dispatches list`              | Lists stored Stripe dispatches.                        | `packages/starter_console/src/starter_console/commands/stripe.py` | Inspect stored events/dispatches.             |
| `starter-console stripe dispatches replay`            | Replays stored dispatches.                             | `packages/starter_console/src/starter_console/commands/stripe.py` | ⚠️ Triggers processing again.                 |
| `starter-console stripe dispatches validate-fixtures` | Validates local Stripe fixture JSON files.             | `packages/starter_console/src/starter_console/commands/stripe.py` | CI-friendly fixture validation.               |

---

## Release & usage

| Command                                   | What it does                                                    | Implementation                            | Notes                               |
| ----------------------------------------- | --------------------------------------------------------------- | ----------------------------------------- | ----------------------------------- |
| `starter-console release db`              | Runs migrations, Stripe seeding, and billing plan verification. | `packages/starter_console/src/starter_console/commands/release.py` | ⚠️ Mutates DB / billing seed state. |
| `starter-console usage sync-entitlements` | Upserts billing plan features from an artifact.                 | `packages/starter_console/src/starter_console/commands/usage.py`   | ⚠️ Writes entitlements/features.    |
| `starter-console usage export-report`     | Generates per-tenant usage dashboard artifacts.                 | `packages/starter_console/src/starter_console/commands/usage.py`   | ⚠️ Writes report artifacts.         |

---

## API & auth utilities

| Command                                                                                | What it does                                  | Implementation                           | Notes                                       |
| -------------------------------------------------------------------------------------- | --------------------------------------------- | ---------------------------------------- | ------------------------------------------- |
| `starter-console api export-openapi --output <PATH>`                                   | Exports the FastAPI OpenAPI schema.           | `packages/starter_console/src/starter_console/commands/api.py`    | ⚠️ Writes output file.                      |
| `starter-console auth tokens issue-service-account --account <SLUG> --scopes <SCOPES>` | Issues a refresh token for a service account. | `packages/starter_console/src/starter_console/commands/auth.py`   | ⚠️ Sensitive output; handle carefully.      |
| `starter-console auth keys rotate`                                                     | Generates a new Ed25519 signing keypair.      | `packages/starter_console/src/starter_console/commands/auth.py`   | ⚠️ Key rotation; affects auth verification. |
| `starter-console auth jwks print`                                                      | Prints current JWKS payload.                  | `packages/starter_console/src/starter_console/commands/auth.py`   | Read-only output.                           |
| `starter-console status subscriptions list`                                            | Lists active status subscriptions.            | `packages/starter_console/src/starter_console/commands/status.py` | Read-only.                                  |
| `starter-console status subscriptions revoke <ID>`                                     | Revokes a subscription.                       | `packages/starter_console/src/starter_console/commands/status.py` | ⚠️ Removes subscription access.             |
| `starter-console status incidents resend <ID>`                                         | Re-dispatches an incident to subscribers.     | `packages/starter_console/src/starter_console/commands/status.py` | ⚠️ Triggers notifications again.            |
| `starter-console util run-with-env <FILES> -- <CMD>`                                   | Merges env files and executes a command.      | `packages/starter_console/src/starter_console/commands/util.py`   | Useful for consistent env layering.         |

---

## Under-the-hood / referenced commands

These are invoked by the CLI and/or referenced in remediation workflows.

| Command                                                                       | What it does                         | Where referenced                                                                                              | Notes                                                  |
| ----------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `just dev-up` / `just dev-down` / `just dev-logs` / `just dev-ps`             | Docker compose dev stack management. | `packages/starter_console/src/starter_console/services/infra/just_targets.py`                                                          | CLI wraps these via `starter-console infra compose …`. |
| `just vault-up` / `just vault-down` / `just vault-logs` / `just verify-vault` | Vault dev server management.         | `packages/starter_console/src/starter_console/services/infra/just_targets.py`                                                          | CLI wraps these via `starter-console infra vault …`.   |
| `just migrate`                                                                | Runs database migrations.            | `packages/starter_console/src/starter_console/services/infra/release_db.py`                                                            | ⚠️ Mutates DB schema.                                  |
| `hatch run serve`                                                             | Starts the backend API service.      | `packages/starter_console/src/starter_console/workflows/home/start/runner.py`                                                          | Used by `starter-console start …` flows.               |
| `pnpm dev --webpack`                                                          | Starts the frontend dev server.      | `packages/starter_console/src/starter_console/workflows/home/start/runner.py`, `packages/starter_console/src/starter_console/workflows/home/probes/frontend.py` | Used by `starter-console start …` flows.               |
