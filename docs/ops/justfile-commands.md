# Justfile Command Reference

This doc summarizes the root `justfile` commands. Run `just help` for the most up-to-date list and
flags. Commands are run from the repo root unless noted.

## Project lifecycle & setup

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just python-bootstrap` | Installs Python 3.11 and Hatch using `uv`. | `justfile` | Requires `uv` installed. |
| `just dev-install` | Installs packages in editable mode. | `justfile` | Installs `starter_contracts`, `starter_providers`, `starter_console`. |
| `just pre-commit-install` | Installs pre-commit hooks. | `justfile` | Installs `pre-commit` if missing. |
| `just bootstrap` | Creates the api-service Hatch env. | `justfile` | Delegates to `apps/api-service/justfile`. |

## Infrastructure (Docker Compose)

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just dev-up` | Starts Postgres, Redis, and optional services (OTel, Vault, MinIO). | `justfile` | Optional services depend on env flags (for example, `ENABLE_OTEL_COLLECTOR`, `ENABLE_MINIO`, `ENABLE_VAULT_DEV`). |
| `just dev-down` | Stops the infrastructure stack. | `justfile` | |
| `just dev-reset` | Stops stack and deletes volumes. | `justfile` | ⚠️ Destructive: deletes local data. |
| `just dev-logs` | Tails infrastructure logs. | `justfile` | Tails last 100 lines. |
| `just dev-ps` | Shows running infrastructure containers. | `justfile` | |
| `just storage-up` | Starts MinIO service only. | `justfile` | |
| `just storage-down` | Stops MinIO service. | `justfile` | |
| `just storage-logs` | Tails MinIO logs. | `justfile` | Tails last 200 lines. |
| `just vault-up` | Starts and initializes Vault dev signer. | `justfile` | Waits for Vault to be ready and runs dev init. |
| `just vault-down` | Stops Vault service. | `justfile` | |
| `just vault-logs` | Tails Vault logs. | `justfile` | Tails last 200 lines. |

## Development & runtime

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just api` | Starts the FastAPI server. | `justfile` | Delegates to `apps/api-service`. |
| `just start-dev` | CLI start: compose + backend + frontend. | `justfile` | Timeout 180s. |
| `just start-backend` | CLI start: backend only. | `justfile` | Timeout 120s. |
| `just start-frontend` | CLI start: frontend only. | `justfile` | Timeout 120s. |
| `just migrate` | Runs Alembic migrations. | `justfile` | Delegates to `apps/api-service`. |
| `just migration-revision "msg"` | Creates a new Alembic revision. | `justfile` | Delegates to `apps/api-service`. |

## Quality assurance & testing

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just lint-all` | Runs linting for backend, CLI, contracts, providers, and web. | `justfile` | Aggregates individual package commands. |
| `just typecheck-all` | Runs typechecking for all packages. | `justfile` | Aggregates individual package commands. |
| `just smoke-http` | Runs API service HTTP smoke suite. | `justfile` | Starts local server via delegation. |
| `just backend-lint` | Lints API service. | `justfile` | Delegates to `apps/api-service`. |
| `just backend-typecheck` | Typechecks API service. | `justfile` | Delegates to `apps/api-service`. |
| `just backend-test` | Tests API service. | `justfile` | Delegates to `apps/api-service`. |
| `just cli-lint` | Lints Starter Console. | `justfile` | Delegates to `packages/starter_console`. |
| `just cli-typecheck` | Typechecks Starter Console. | `justfile` | Delegates to `packages/starter_console`. |
| `just cli-test` | Tests Starter Console. | `justfile` | Delegates to `packages/starter_console`. |
| `just contracts-lint` | Lints Contracts package. | `justfile` | Delegates to `packages/starter_contracts`. |
| `just contracts-typecheck` | Typechecks Contracts package. | `justfile` | Delegates to `packages/starter_contracts`. |
| `just contracts-test` | Tests Contracts package. | `justfile` | Delegates to `packages/starter_contracts`. |
| `just providers-lint` | Lints Providers package. | `justfile` | Delegates to `packages/starter_providers`. |
| `just providers-typecheck` | Typechecks Providers package. | `justfile` | Delegates to `packages/starter_providers`. |
| `just providers-test` | Tests Providers package. | `justfile` | Delegates to `packages/starter_providers`. |
| `just web-lint` | Lints Web App. | `justfile` | Delegates to `apps/web-app`. |
| `just web-typecheck` | Typechecks Web App. | `justfile` | Delegates to `apps/web-app`. |
| `just web-build` | Builds Web App. | `justfile` | Delegates to `apps/web-app`. |
| `just web-dev` | Starts Web App dev server. | `justfile` | Delegates to `apps/web-app`. |
| `just web-test` | Tests Web App. | `justfile` | Delegates to `apps/web-app`. |

## Data, auth, and wizards

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just setup-demo-lite` | Runs demo setup wizard (lite profile). | `justfile` | Uses the CLI wizard; skips GeoIP + Stripe. |
| `just setup-demo-full` | Runs demo setup wizard (full profile). | `justfile` | Uses the CLI wizard; enables GeoIP + Stripe. |
| `just setup-staging` | Runs setup wizard for staging. | `justfile` | Uses staging profile and answer flags when provided. |
| `just setup-production` | Runs setup wizard for production. | `justfile` | Requires `setup_production_answers` with `--strict`. |
| `just seed-dev-user` | Seeds a developer account in the DB. | `justfile` | Uses configured user/tenant vars. |
| `just issue-demo-token` | Issues a service-account token. | `justfile` | Requires running API; outputs JSON. |
| `just verify-vault` | Verifies Vault setup by issuing a service account token. | `justfile` | Requires running API. |

## Utilities & CLI helpers

| Command | What it does | Implementation / Source | Notes |
| ------- | ------------ | ----------------------- | ----- |
| `just doctor` | Generates a system health report. | `justfile` | Writes JSON and Markdown to `var/reports/`. |
| `just openapi-export` | Exports OpenAPI JSON artifacts. | `justfile` | Writes `apps/api-service/.artifacts/openapi*.json`. |
| `just stripe-replay args` | Replays Stripe dispatches via CLI. | `justfile` | Example: `just stripe-replay args="list --status failed"`. |
| `just stripe-listen` | Captures Stripe webhook secret. | `justfile` | Runs `starter-console stripe webhook-secret`. |
| `just lint-stripe-fixtures` | Validates Stripe fixtures. | `justfile` | Uses `starter-console stripe dispatches validate-fixtures`. |
| `just test-stripe` | Runs pytest with `stripe_replay` marker. | `justfile` | Runs in `apps/api-service`. |
| `just cli cmd` | Runs arbitrary Starter Console commands. | `justfile` | Example: `just cli cmd="users ensure-dev --email dev@example.com"`. |
