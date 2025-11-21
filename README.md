# OpenAI Agent Starter

Production-ready starter kit for building AI Agent SaaS products. The repo bundles a FastAPI backend (OpenAI Agents SDK v0.5.0) and a Next.js 15 frontend, plus an operator-focused Starter CLI that wires secrets, infrastructure, and env files in one flow.

## Architecture At A Glance
- **Backend** (`api-service/`): FastAPI, async SQLAlchemy, Postgres + Redis (refresh tokens & billing), JWT auth, Alembic migrations, Ed25519 keys in `var/keys/`, OpenAI Agents SDK integrations, Stripe billing services.
- **Frontend** (`web-app/`): Next.js 15, TanStack Query, Shadcn UI, HeyAPI-generated client under `lib/api/client`.
- **Starter CLI** (`starter_cli/`): Operator workflows (setup wizard, secrets onboarding, Stripe provisioning, auth tooling, infra helpers) with side-effect-free imports so CI/CD can run `python -m starter_cli.app`.
- **Docs & Trackers** (`docs/`): SDK references, frontend UI/data-access guides, CLI milestones, and project trackers.

## Prerequisites
| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.11+ | Install backend extras: `pip install 'api-service[dev]'`. |
| Hatch | Latest | Manages backend virtualenv + scripts. |
| Node.js | 20+ | Paired with `pnpm` for the Next.js app. |
| pnpm | 8+ | `pnpm install` in `web-app/`. |
| just | Latest | Task runner replacing the old Makefile; install via `brew install just` or `sudo apt-get install just`. |
| Docker & Compose v2 | — | Used by Just recipes for Postgres/Redis/Vault. |
| Stripe CLI | — | Required for `starter_cli stripe setup` unless `--skip-stripe-cli`. |

> Tip: macOS users can run `brew install just`; Ubuntu runners can use `sudo apt-get install just`.

## First-Time Setup
1. **Bootstrap tooling**  
   ```bash
   just bootstrap          # creates/refreshes the Hatch environment
   pnpm install            # inside web-app/
   ```
2. **Run prerequisite check**  
   ```bash
   python -m starter_cli.app infra deps --format table
   ```
3. **Guided environment wizard**  
   ```bash
   python -m starter_cli.app setup wizard --profile local
   # OR: just cli cmd="setup wizard --profile local"
   ```  
   The wizard writes `.env.local` (backend) and `web-app/.env.local`, covering secrets, providers, tenants, signup policy, and frontend runtime config. Use `--non-interactive`, `--answers-file`, and `--summary-path` for headless or auditable runs.
4. **Bring up local infrastructure**  
   ```bash
   just dev-up        # Postgres + Redis
   just vault-up      # optional: dev Vault signer for auth flows
   ```

## Running The Stack
- **Backend API**  
  ```bash
  just api
  ```  
  Wraps `hatch run serve` with `.env.compose` + `.env.local`. Use `just migrate` / `just migration-revision message="add_users"` for Alembic workflows.

- **Frontend App**  
  ```bash
  cd web-app
  pnpm dev
  ```
  Env is pulled from `web-app/.env.local`. Follow `docs/frontend/data-access.md` and `docs/frontend/ui/components.md` for feature architecture and Shadcn usage.

## Starter CLI Highlights
All commands run via `python -m starter_cli.app …` or `just cli cmd='…'`.
- `setup wizard` – milestone-based env bootstrap (Secrets → Providers → Observability → Signup → Frontend).
- `secrets onboard` – guided workflows for Vault (dev/HCP), Infisical, AWS Secrets Manager, Azure Key Vault; validates connectivity before emitting env updates.
- `stripe setup` – provisioning for `starter` and `pro` plans, captures webhook + secret keys, can run headless with `--non-interactive`.
- `auth` – service-account token issuance, Ed25519 key rotation, JWKS printing (uses Vault transit when enabled).
- `infra` – wraps `just dev-*` and `just vault-*` plus dependency checks.
- `status` – manages `/api/v1/status` subscriptions/incidents.
- `config dump-schema` – audits every FastAPI setting with env alias, default, type, and wizard coverage.
- `home` / `doctor` – probe-driven health with TUI. Probes are grouped by category (core, secrets, billing) and can be suppressed intentionally via `EXPECT_API_DOWN`, `EXPECT_FRONTEND_DOWN`, `EXPECT_DB_DOWN`, `EXPECT_REDIS_DOWN` (logged once at startup, not shown in the TUI). Services panel collapses when it would duplicate backend/frontend probes; probes remain the source of truth in TUI and JSON/Markdown reports.

Refer to `starter_cli/README.md` for detailed flags, answers-file formats, and contribution rules (imports must stay side-effect free; new env knobs require inventory + tracker updates).

## Automation & Reporting
- `setup wizard` now supports automation toggles (`--auto-infra`, `--auto-secrets`, `--auto-stripe`) plus dependency-aware gating so you can spin up Docker/Redis, manage the local Vault dev signer, and run Stripe provisioning directly from the CLI.
- Every run emits:
  - `var/reports/setup-summary.json` — machine-readable milestone report.
  - `var/reports/cli-one-stop-summary.md` — resume-ready Markdown recap (profile, automation status, verification snapshot).
  - `var/reports/verification-artifacts.json` — append-only ledger of provider verification artifacts (Vault transit probes, AWS/Azure/Infisical checks, Stripe seeding).
- Use these artifacts to prove the environment was bootstrapped correctly (attach the Markdown snippet to onboarding tickets or demos).

## Development Workflow
- Keep FastAPI routers <300 lines; extract shared helpers once reused.
- Redis is dual-use: refresh-token cache and billing event transport. Coordinate settings through the wizard or `.env.local`.
- Secrets live in `var/keys/`; Vault workflows (`just vault-up`, `just verify-vault`) help issue signed tokens locally.
- Tests are SQLite + fakeredis by default (`conftest.py`); avoid leaking env mutations between tests.
- Backend edits → `hatch run lint` & `hatch run pyright`; frontend edits → `pnpm lint` & `pnpm type-check`.

## Key References
- `starter_cli/README.md` – CLI deep dive, command catalog.
- `SNAPSHOT.md` / `starter_cli/SNAPSHOT.md` – architecture overviews for the repo and CLI.
- `docs/openai-agents-sdk/` – SDK reference + integration patterns.
- `docs/frontend/data-access.md` & `docs/frontend/ui/components.md` – frontend architecture + component inventory.
- `docs/trackers/CLI_MILESTONE.md` – CLI roadmap and status.
- `docs/ops/usage-guardrails-runbook.md` – plan-aware usage guardrails enablement, metrics, and troubleshooting steps.
- `python -m starter_cli.app usage sync-entitlements` – CLI helper that syncs `var/reports/usage-entitlements.json` into `plan_features` so guardrails enforce the latest plan limits.
- `justfile` – curated commands for API, migrations, infra, Stripe tooling, and CLI invocation.

> Future sections can expand on backend internals, service boundaries, and frontend feature guides as they are reviewed. For now, use this README as the top-level map and follow the linked docs for deeper dives.
