# Starter CLI

The Starter CLI is the operator entrypoint for the OpenAI Agents Starter stack. It bootstraps
FastAPI + Next.js deployments by collecting environment variables, wiring secrets providers,
provisioning Stripe assets, and exposing admin utilities for authentication, status alerts, and
local infrastructure. All commands run through the same configuration layer as the backend, so the
values written here are exactly what FastAPI and the CLI share at runtime.

> **Directory map:** for a full code walkthrough, see `starter_cli/SNAPSHOT.md`.

## Prerequisites & Invocation

- Python 3.11+, Hatch, and the backend dev dependencies (`pip install 'api-service[dev]'`).
- Node.js 20+ and `pnpm` (for the frontend env file that the wizard populates).
- Docker + Docker Compose v2 (for `just dev-up` / `just vault-up`).
- `just` task runner (install via `brew install just` or `sudo apt-get install just`).
- Stripe CLI (required for `stripe setup` unless you pass `--skip-stripe-cli`).

From the repo root run:

```bash
python -m starter_cli.app --help
```

> The legacy `starter_cli.cli` shim has been removed; use `python -m starter_cli.app` going forward.

Environment loading rules:

1. By default the CLI loads `.env.compose`, `.env`, and `.env.local` in that order (see
   `starter_cli/core/context.py`).
2. Use `--env-file PATH` to append additional env files.
3. Pass `--skip-env` (or export `STARTER_CLI_SKIP_ENV=true`) to rely solely on explicit
   `--env-file` arguments or the current shell.
4. Quiet logs from env loading via `--quiet-env`.

Most subcommands support headless execution. Provide answers via one or more JSON files
(`--answers-file path/to/answers.json`) or individual overrides (`--var KEY=VALUE`).

## Command Catalog

### 1. `setup wizard`

Guided setup that writes `.env.local` (backend) and, when present, `web-app/.env.local`.
The flow covers five milestones plus frontend wiring:

| Milestone | Focus | Key outputs |
| --- | --- | --- |
| M1 Secrets & Vault | Generate peppers/keys, optionally rotate Ed25519 material, enforce Vault transit verification | `SECRET_KEY`, `AUTH_*` peppers, `VAULT_*` vars |
| M2 Providers & Infra | Database URL, AI providers, Redis pools, Stripe, Resend, migrations | `DATABASE_URL`, `OPENAI_API_KEY`, `REDIS_URL`, `RATE_LIMIT_REDIS_URL`, `AUTH_CACHE_REDIS_URL`, `SECURITY_TOKEN_REDIS_URL`, `BILLING_EVENTS_REDIS_URL`, `STRIPE_*`, `RESEND_*` |
| M3 Tenant & Observability | Tenant defaults, logging sinks, GeoIP providers | `TENANT_DEFAULT_SLUG`, `LOGGING_*`, `GEOIP_*` |
| M4 Integrations | Slack status notifications (bot token, channel targets, optional test ping) | `ENABLE_SLACK_STATUS_NOTIFICATIONS`, `SLACK_STATUS_BOT_TOKEN`, `SLACK_STATUS_DEFAULT_CHANNELS`, `SLACK_STATUS_TENANT_CHANNEL_MAP` |
| M5 Signup & Worker policy | Signup posture (policy + throttles) plus billing retry worker | `SIGNUP_ACCESS_POLICY`, `ALLOW_PUBLIC_SIGNUP`, `SIGNUP_RATE_LIMIT_PER_*`, `SIGNUP_CONCURRENT_REQUESTS_LIMIT`, `BILLING_RETRY_DEPLOYMENT_MODE`, `ENABLE_BILLING_RETRY_WORKER` |
| Frontend | Next.js runtime config | `NEXT_PUBLIC_API_URL`, Playwright URL, cookie flags |

GeoIP prompts cover IPinfo/IP2Location SaaS tokens plus self-hosted MaxMind/IP2Location databases. When you choose the MaxMind database provider, the wizard can download/refresh the GeoLite2 City bundle (using `GEOIP_MAXMIND_LICENSE_KEY`) and will warn if the on-disk `.mmdb` file is missing. Cache TTL/capacity and HTTP timeout knobs are recorded alongside the provider choice so backend services stay in sync with operator expectations.

#### Interactive shell

Interactive runs now open with a shell-style home screen instead of dropping you straight into prompts. The panel shows every section, its completion state, and the next recommended milestone. Commands:

- `Enter` — jump to the next incomplete section.
- `1-8` — open that section immediately.
- `Q` — quit without finalizing (you can resume later; answers are saved incrementally).
- Section keys (e.g., `secrets`) also work as shortcuts.

Once all sections show `Done`, press `Enter` to finalize or reopen any section for edits. Pass `--legacy-flow` (or `--no-tui`) to return to the previous linear experience.

Flags:

- `--profile {local,staging,production}` toggles defaults and required checks.
- `--strict` forces headless runs for production (auto-enables `--non-interactive` and rejects missing answers).
- `--non-interactive` + `--answers-file/--var` run headless.
- `--export-answers PATH` writes every prompt response from the current run to JSON so you can replay/edit it later.
- `--report-only` skips prompts and prints the milestone audit without modifying env files.
- `--output {summary,json,checklist}` selects the console format. `checklist` emits a Markdown
  checklist that you can pipe to a file or pair with `--markdown-summary-path`.
- `--legacy-flow` forces the legacy linear prompts (disables the new shell dashboard).
- `--summary-path PATH` writes the audit JSON (defaults to `var/reports/setup-summary.json`).
- `--auto-infra/--no-auto-infra`, `--auto-secrets/--no-auto-secrets`, and `--auto-stripe/--no-auto-stripe` opt in or out of the legacy automation hooks (Docker compose, Vault dev signer, embedded Stripe provisioning).
- `--auto-migrations/--no-auto-migrations`, `--auto-redis/--no-auto-redis`, and `--auto-geoip/--no-auto-geoip` control the new automation phases for database migrations, Redis warm-up, and GeoIP dataset downloads.
- `--markdown-summary-path PATH` writes a Markdown recap (defaults to `var/reports/cli-one-stop-summary.md`).
  When combined with `--report-only --output checklist`, the CLI writes the checklist directly to the
  provided path so Platform Foundations can drop it into trackers.
- `--no-schema` bypasses the dependency graph (legacy linear prompts). `--no-tui` disables both the interactive shell and the legacy Rich dashboard, falling back to plain console logs (CI, piping, etc.).

Artifacts generated per run:

- `var/reports/setup-summary.json` — serialized milestone + automation summary.
- `var/reports/cli-one-stop-summary.md` — Markdown snippet with automation status, verification notes, and milestone table.
- `var/reports/verification-artifacts.json` — append-only ledger of provider verifications (Vault, AWS, Azure, Infisical, Stripe). This is cumulative across runs.
- `var/reports/wizard-state.json` — cached prompt outcomes feeding the dependency graph; delete it when you want a totally fresh interaction.

#### Profiles & Answer Files

1. Run the wizard interactively with `--profile local` to gather every required value.
2. Pass `--export-answers ops/environments/local.json` so the CLI writes the actual responses you just entered.
3. Duplicate that file per environment (`staging.json`, `production.json`), scrub or swap any secrets, and check them into your secure config repo.
4. Replay the wizard headlessly with `python -m starter_cli.app setup wizard --profile staging --non-interactive --answers-file ops/environments/staging.json`.
5. For hardened runs, add `--strict` (production only) so the CLI refuses to prompt and enforces that every answer is pre-supplied.

This workflow keeps a single schema-driven wizard while avoiding ad-hoc copying of `.env.local` files between environments.

#### Dashboard + Dependency Graph

- The wizard now streams a Rich dashboard (milestones, automation phases, rolling activity log). Disable with `--no-tui` if you need minimal output.
- Prompts are driven by `starter_cli/workflows/setup/schema.yaml`, so Vault/Slack/GeoIP/billing worker questions only appear when prerequisites are satisfied—even in headless runs.
- Automation phases emit progress to the dashboard and audit summaries. Docker/Vault/Stripe automation existed before; migrations, Redis warm-up, and GeoIP downloads now ride the same rails with automatic retries + remediation notes.
- The exit checklist leaves only two manual steps: `hatch run serve` (backend) and `pnpm dev` (frontend). You can opt to keep Docker Compose running so those commands work immediately; otherwise the wizard tears down infra during cleanup.

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
4. Optionally runs helper Just recipes (e.g., `just vault-up`).

### 3. `stripe setup`

Interactive provisioning of Stripe products/prices plus secret capture:

- Verifies the `stripe` Python package and Stripe CLI are present (unless `--skip-stripe-cli`).
- Optionally runs `just dev-up` and tests `psql` connectivity before seeding plan data.
- Prompts for secret key/webhook secret (or requires `--secret-key/--webhook-secret` in
  `--non-interactive` mode). Interactive runs can now generate the webhook signing secret via
  `stripe listen --print-secret --forward-to http://localhost:8000/api/v1/webhooks/stripe` using
  `--auto-webhook-secret` or the wizard prompt (local profile).
- Ensures one product & price per plan (`starter`, `pro`) in Stripe and writes
  `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRODUCT_PRICE_MAP`, and `ENABLE_BILLING=true`
  into `.env.local`, plus `NEXT_PUBLIC_ENABLE_BILLING=true` into `web-app/.env.local` when present.

Convenience command: `python -m starter_cli.app stripe webhook-secret --forward-url <url>` (also
available as `just stripe-listen`) captures the signing secret via Stripe CLI and writes it to
`.env.local`.

Useful flags: `--currency`, `--trial-days`, `--plan code=amount`, `--skip-postgres-check`.

### 4. `auth`

Operator utilities around authentication:

- `auth tokens issue-service-account`: calls FastAPI’s `/api/v1/auth/service-accounts/issue` with a
  Vault-signed envelope to mint refresh tokens for service accounts.
- `auth keys rotate`: generates a new Ed25519 keypair, persists it through the shared key storage
  (Vault/dev keyset), and prints the JWKS payload.
- `auth jwks print`: materializes the current JWKS.

### 5. `infra`

Wraps Just recipes for local infrastructure and dependency checks:

- `infra compose {up,down,logs,ps}` → `just dev-*` recipes for Postgres + Redis.
- `infra vault {up,down,logs,verify}` → `just vault-*` helpers for the dev signer.
- `infra deps [--format {table,json}]` → verifies Docker, Compose v2, Hatch, Node, pnpm.

### 6. `status`

Manages the `/api/v1/status` surface:

- `status subscriptions list|revoke` for alert subscriptions (requires `STATUS_API_TOKEN`).
- `status incidents resend` to redispatch a stored incident (optionally by tenant and severity).

### 7. `providers validate`

Validates Stripe, Resend, and Tavily configuration before you boot FastAPI or deploy:

- Loads the same env files as other commands, reuses the backend validator, and prints one line per
  violation with provider/code context.
- Returns non-zero when fatal issues exist (any hardened environment or when you pass `--strict`).
- Use `just validate-providers` or `python -m starter_cli.app providers validate --strict` in CI to
  fail the pipeline before Docker builds or migrations.

### 8. `usage`

Guardrail-focused operator helpers:

- `usage sync-entitlements` — ingests `var/reports/usage-entitlements.json` and upserts plan
  features into Postgres/Stripe so the backend enforces the latest limits. Supports `--dry-run`,
  `--plan starter --plan pro`, and `--prune-missing` to delete retired features.
- `usage export-report` — queries tenant subscriptions + rollups and writes dashboard artifacts
  (JSON/CSV) under `var/reports/usage-dashboard.*` by default. Filters: `--tenant slug`, `--plan code`,
  `--feature key`, `--period-start/-end`, and `--include-inactive`. Operators can dial the warn
  threshold (`--warn-threshold 0.75`) and redirect or disable specific artifacts via
  `--output-json PATH`, `--output-csv PATH`, `--no-json`, or `--no-csv`.

### 9. `config dump-schema`

Renders every FastAPI setting and its env alias, default, type, and wizard coverage. Use this to audit
what remains unprompted after running the wizard. Supports `--format table` (default) or `json`.

### 10. `release db`

End-to-end release helper that enforces the migration → Stripe provisioning → billing verification order.

```bash
python -m starter_cli.app release db \
  --summary-path var/reports/db-release-$(date -u +%Y%m%dT%H%M%SZ).json
```

What it does:

1. Runs `just migrate` with the current `.env*` context.
2. Captures the Alembic head via `hatch run alembic -c api-service/alembic.ini current`.
3. Invokes the existing Stripe setup flow unless `--skip-stripe` is passed.
4. Queries `billing_plans` to ensure each plan is active and has a Stripe price ID.
5. Writes `var/reports/db-release-*.json` with timestamps, git SHA, masked secrets, plan statuses, and the flags used (pass `--json` to also print it to stdout).

Flags:

- `--non-interactive` – fail instead of prompting; combine with `--plan starter=2000 --plan pro=9900` (or your catalog) when headless.
- `--skip-stripe` / `--skip-db-checks` – opt out of the Stripe provisioning or SQL verification phases when manual evidence is provided elsewhere.
- `--plan CODE=CENTS` – forwarded to the embedded Stripe flow and required per plan when `--non-interactive` is used.

See `docs/ops/db-release-playbook.md` for the full pre-flight checklist, evidence expectations, and rollback guidance.

## Headless & CI Patterns

- **Answers file format:** JSON object of `KEY: "value"`. Keys are uppercased internally.
- **Export helper:** add `--export-answers path/to/local.json` to an interactive run to capture everything you typed so the exact payload can be reused (after edits) in staging/production.
- **Billing retry worker:** Headless runs *must* include `BILLING_RETRY_DEPLOYMENT_MODE` (`inline` or `dedicated`). The former `ENABLE_BILLING_RETRY_WORKER` flag is ignored and the wizard will exit with an error if the new key is missing.
- **Override precedence:** later `--answers-file` entries overwrite earlier ones; `--var` entries win
  last.
- **Detection:** the wizard sets `context.is_headless` when answers are present so it can skip
  interactive-only helpers (e.g., Stripe seeding prompt).
- **Common CI flow:** `python -m starter_cli.app setup wizard --profile staging --non-interactive \
  --answers-file ops/environments/staging.json --summary-path artifacts/setup-summary.json`.

## Generated Outputs & Reference Material

- `.env.local` (backend) and `web-app/.env.local` are written via
  `starter_cli/adapters/env/files.py`.
- Milestone reports live in `var/reports/setup-summary.json` unless overridden.
- Wizard coverage of backend env vars is tracked in `starter_cli/core/inventory.py`.
- Provider runners and supporting models are under `starter_cli/workflows/secrets/`.
- CLI architectural snapshot: `starter_cli/SNAPSHOT.md`.

## Contribution Guidelines

- Imports must remain side-effect free (`python -m starter_cli.app` should not hit external services).
- Tests stub network calls; `conftest.py` forces SQLite/fakeredis—new modules must obey that contract.
- Any new CLI workflow that introduces env knobs should update `starter_cli/core/inventory.py` *and*
  the relevant tracker under `docs/trackers/` (e.g., `CLI_MILESTONE.md`).
- Follow the repo-wide tooling expectations after edits: run backend `hatch run lint` /
  `hatch run pyright` or frontend `pnpm lint` / `pnpm type-check` when you touch those surfaces from a
  CLI workflow.

## Suggested Next Steps

1. Run `python -m starter_cli.app infra deps` to confirm prerequisites.
2. Execute `python -m starter_cli.app setup wizard --profile local` for a new checkout.
3. Use `starter_cli/commands/stripe.py` as a reference when onboarding billing.
4. Review `docs/trackers/CLI_MILESTONE.md` before adding new features to ensure roadmap parity.
