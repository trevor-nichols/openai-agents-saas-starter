# Starter CLI

The Starter CLI is the operator entrypoint for the OpenAI Agents Starter stack. It bootstraps
FastAPI + Next.js deployments by collecting environment variables, wiring secrets providers,
provisioning Stripe assets, and exposing admin utilities for authentication, status alerts, and
local infrastructure. All commands run through the same configuration layer as the backend, so the
values written here are exactly what FastAPI and the CLI share at runtime.

> **Directory map:** for a full code walkthrough, see `starter_cli/SNAPSHOT.md`.

## Prerequisites & Invocation

- Python 3.11+, Hatch, and the backend dev dependencies (`pip install 'anything-agents[dev]'`).
- Node.js 20+ and `pnpm` (for the frontend env file that the wizard populates).
- Docker + Docker Compose v2 (for `make dev-up` / `make vault-up`).
- Stripe CLI (required for `stripe setup` unless you pass `--skip-stripe-cli`).

From the repo root run:

```bash
python -m starter_cli.cli --help
```

Environment loading rules:

1. By default the CLI loads `.env.compose`, `.env`, and `.env.local` in that order (see
   `starter_cli/cli/common.py`).
2. Use `--env-file PATH` to append additional env files.
3. Pass `--skip-env` (or export `STARTER_CLI_SKIP_ENV=true`) to rely solely on explicit
   `--env-file` arguments or the current shell.
4. Quiet logs from env loading via `--quiet-env`.

Most subcommands support headless execution. Provide answers via one or more JSON files
(`--answers-file path/to/answers.json`) or individual overrides (`--var KEY=VALUE`).

## Command Catalog

### 1. `setup wizard`

Guided setup that writes `.env.local` (backend) and, when present, `agent-next-15-frontend/.env.local`.
The flow covers four milestones plus frontend wiring:

| Milestone | Focus | Key outputs |
| --- | --- | --- |
| M1 Secrets & Vault | Generate peppers/keys, optionally rotate Ed25519 material, enforce Vault transit verification | `SECRET_KEY`, `AUTH_*` peppers, `VAULT_*` vars |
| M2 Providers & Infra | Database URL, AI providers, Redis, Stripe, Resend, migrations | `DATABASE_URL`, `OPENAI_API_KEY`, `REDIS_URL`, `STRIPE_*`, `RESEND_*` |
| M3 Tenant & Observability | Tenant defaults, logging sinks, GeoIP providers | `TENANT_DEFAULT_SLUG`, `LOGGING_*`, `GEOIP_*` |
| M4 Signup & Worker policy | Signup posture (policy + throttles) plus billing retry worker | `SIGNUP_ACCESS_POLICY`, `ALLOW_PUBLIC_SIGNUP`, `SIGNUP_RATE_LIMIT_PER_*`, `SIGNUP_CONCURRENT_REQUESTS_LIMIT`, `ENABLE_BILLING_RETRY_WORKER` |
| Frontend | Next.js runtime config | `NEXT_PUBLIC_API_URL`, Playwright URL, cookie flags |

Flags:

- `--profile {local,staging,production}` toggles defaults and required checks.
- `--non-interactive` + `--answers-file/--var` run headless.
- `--report-only` skips prompts and prints the milestone audit without modifying env files.
- `--output {summary,json}` selects console format.
- `--summary-path PATH` writes the audit JSON (defaults to `var/reports/setup-summary.json`).
- `--auto-infra/--no-auto-infra`, `--auto-secrets/--no-auto-secrets`, and `--auto-stripe/--no-auto-stripe` opt in or out of the automation hooks. Today that covers Docker compose (Postgres/Redis), the local Vault dev signer used for transit verification, and the embedded Stripe provisioning flow. When omitted, the wizard prompts for each phase and records the decision in the audit.
- `--markdown-summary-path PATH` writes a Markdown recap (defaults to `var/reports/cli-one-stop-summary.md`). Use it when you want to drop the summary into issues or onboarding docs.

Artifacts generated per run:

- `var/reports/setup-summary.json` — serialized milestone + automation summary.
- `var/reports/cli-one-stop-summary.md` — Markdown snippet with automation status, verification notes, and milestone table.
- `var/reports/verification-artifacts.json` — append-only ledger of provider verifications (Vault, AWS, Azure, Infisical, Stripe). This is cumulative across runs.

### Tenant IDs & Conversation APIs

Conversation storage no longer auto-creates a "default" tenant. After the wizard captures the slug (`TENANT_DEFAULT_SLUG`), run `scripts/seed_users.py` (or your tenant provisioning workflow). Once the database contains at least one tenant, rerunning the wizard (or finishing another run) will automatically surface the matching tenant UUID—copy it into your operator docs/CI secrets so API clients can populate the `tenant_id` claim or `X-Tenant-Id` header. Without that scope, `/api/v1/chat` and `/api/v1/conversations` now reject the request before it reaches the agent service. Keep at least one tenant UUID handy for CI smoke tests and staging operators.


After prompting, the wizard reloads the environment and clears cached settings so subsequent CLI
commands see the fresh values.

### 2. `secrets onboard`

Onboards a hosted secrets/signing provider. Available runners today: Vault Dev, HCP Vault, Infisical
(Cloud & Self-hosted), AWS Secrets Manager, and Azure Key Vault. Each workflow:

1. Prompts (or reads headless answers) for provider-specific values.
2. Validates connectivity (e.g., Vault transit probe, AWS `GetSecretValue`, Azure Key Vault reads,
   Infisical API check).
3. Prints env updates + next steps so you can copy them into `.env.local` or CI secrets.
4. Optionally runs helper Makefile targets (e.g., `make vault-up`).

### 3. `stripe setup`

Interactive provisioning of Stripe products/prices plus secret capture:

- Verifies the `stripe` Python package and Stripe CLI are present (unless `--skip-stripe-cli`).
- Optionally runs `make dev-up` and tests `psql` connectivity before seeding plan data.
- Prompts for secret key/webhook secret (or requires `--secret-key/--webhook-secret` in
  `--non-interactive` mode).
- Ensures one product & price per plan (`starter`, `pro`) in Stripe and writes
  `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRODUCT_PRICE_MAP`, and `ENABLE_BILLING=true`
  into `.env.local`.

Useful flags: `--currency`, `--trial-days`, `--plan code=amount`, `--skip-postgres-check`.

### 4. `auth`

Operator utilities around authentication:

- `auth tokens issue-service-account`: calls FastAPI’s `/api/v1/auth/service-accounts/issue` with a
  Vault-signed envelope to mint refresh tokens for service accounts.
- `auth keys rotate`: generates a new Ed25519 keypair, persists it through the shared key storage
  (Vault/dev keyset), and prints the JWKS payload.
- `auth jwks print`: materializes the current JWKS.

### 5. `infra`

Wraps Make targets for local infrastructure and dependency checks:

- `infra compose {up,down,logs,ps}` → `make dev-*` targets for Postgres + Redis.
- `infra vault {up,down,logs,verify}` → `make vault-*` helpers for the dev signer.
- `infra deps [--format {table,json}]` → verifies Docker, Compose v2, Hatch, Node, pnpm.

### 6. `status`

Manages the `/api/v1/status` surface:

- `status subscriptions list|revoke` for alert subscriptions (requires `STATUS_API_TOKEN`).
- `status incidents resend` to redispatch a stored incident (optionally by tenant and severity).

### 7. `config dump-schema`

Renders every FastAPI setting and its env alias, default, type, and wizard coverage. Use this to audit
what remains unprompted after running the wizard. Supports `--format table` (default) or `json`.

## Headless & CI Patterns

- **Answers file format:** JSON object of `KEY: "value"`. Keys are uppercased internally.
- **Override precedence:** later `--answers-file` entries overwrite earlier ones; `--var` entries win
  last.
- **Detection:** the wizard sets `context.is_headless` when answers are present so it can skip
  interactive-only helpers (e.g., Stripe seeding prompt).
- **Common CI flow:** `python -m starter_cli.cli setup wizard --profile staging --non-interactive \
  --answers-file ops/environments/staging.json --summary-path artifacts/setup-summary.json`.

## Generated Outputs & Reference Material

- `.env.local` (backend) and `agent-next-15-frontend/.env.local` are written via
  `starter_cli/cli/env.py`.
- Milestone reports live in `var/reports/setup-summary.json` unless overridden.
- Wizard coverage of backend env vars is tracked in `starter_cli/cli/inventory.py`.
- Provider runners and supporting models are under `starter_cli/cli/secrets/`.
- CLI architectural snapshot: `starter_cli/SNAPSHOT.md`.

## Contribution Guidelines

- Imports must remain side-effect free (`python -m starter_cli.cli` should not hit external services).
- Tests stub network calls; `conftest.py` forces SQLite/fakeredis—new modules must obey that contract.
- Any new CLI workflow that introduces env knobs should update `starter_cli/cli/inventory.py` *and*
  the relevant tracker under `docs/trackers/` (e.g., `CLI_MILESTONE.md`).
- Follow the repo-wide tooling expectations after edits: run backend `hatch run lint` /
  `hatch run pyright` or frontend `pnpm lint` / `pnpm type-check` when you touch those surfaces from a
  CLI workflow.

## Suggested Next Steps

1. Run `python -m starter_cli.cli infra deps` to confirm prerequisites.
2. Execute `python -m starter_cli.cli setup wizard --profile local` for a new checkout.
3. Use `starter_cli/cli/stripe_commands.py` as a reference when onboarding billing.
4. Review `docs/trackers/CLI_MILESTONE.md` before adding new features to ensure roadmap parity.
