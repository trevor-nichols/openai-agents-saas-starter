# OpenAI Agent Starter

Production-ready starter kit for building AI Agent SaaS products. The repo bundles a FastAPI backend (OpenAI Agents SDK v0.5.0) and a Next.js 15 frontend, plus an operator-focused Starter CLI that wires secrets, infrastructure, and env files in one flow.

## Architecture At A Glance
- **Backend** (`anything-agents/`): FastAPI, async SQLAlchemy, Postgres + Redis (refresh tokens & billing), JWT auth, Alembic migrations, Ed25519 keys in `var/keys/`, OpenAI Agents SDK integrations, Stripe billing services.
- **Frontend** (`agent-next-15-frontend/`): Next.js 15, TanStack Query, Shadcn UI, HeyAPI-generated client under `lib/api/client`.
- **Starter CLI** (`starter_cli/`): Operator workflows (setup wizard, secrets onboarding, Stripe provisioning, auth tooling, infra helpers) with side-effect-free imports so CI/CD can run `python -m starter_cli.cli`.
- **Docs & Trackers** (`docs/`): SDK references, frontend UI/data-access guides, CLI milestones, and project trackers.

## Prerequisites
| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.11+ | Install backend extras: `pip install 'anything-agents[dev]'`. |
| Hatch | Latest | Manages backend virtualenv + scripts. |
| Node.js | 20+ | Paired with `pnpm` for the Next.js app. |
| pnpm | 8+ | `pnpm install` in `agent-next-15-frontend/`. |
| Docker & Compose v2 | — | Used by Make targets for Postgres/Redis/Vault. |
| Stripe CLI | — | Required for `starter_cli stripe setup` unless `--skip-stripe-cli`. |

## First-Time Setup
1. **Bootstrap tooling**  
   ```bash
   make bootstrap          # creates/refreshes the Hatch environment
   pnpm install            # inside agent-next-15-frontend/
   ```
2. **Run prerequisite check**  
   ```bash
   python -m starter_cli.cli infra deps --format table
   ```
3. **Guided environment wizard**  
   ```bash
   python -m starter_cli.cli setup wizard --profile local
   # OR: make cli CMD="setup wizard --profile local"
   ```  
   The wizard writes `.env.local` (backend) and `agent-next-15-frontend/.env.local`, covering secrets, providers, tenants, signup policy, and frontend runtime config. Use `--non-interactive`, `--answers-file`, and `--summary-path` for headless or auditable runs.
4. **Bring up local infrastructure**  
   ```bash
   make dev-up        # Postgres + Redis
   make vault-up      # optional: dev Vault signer for auth flows
   ```

## Running The Stack
- **Backend API**  
  ```bash
  make api
  ```  
  Wraps `hatch run serve` with `.env.compose` + `.env.local`. Use `make migrate` / `make migration-revision MESSAGE=...` for Alembic workflows.

- **Frontend App**  
  ```bash
  cd agent-next-15-frontend
  pnpm dev
  ```
  Env is pulled from `agent-next-15-frontend/.env.local`. Follow `docs/frontend/data-access.md` and `docs/frontend/ui/components.md` for feature architecture and Shadcn usage.

## Starter CLI Highlights
All commands run via `python -m starter_cli.cli …` or `make cli CMD='…'`.
- `setup wizard` – milestone-based env bootstrap (Secrets → Providers → Observability → Signup → Frontend).
- `secrets onboard` – guided workflows for Vault (dev/HCP), Infisical, AWS Secrets Manager, Azure Key Vault; validates connectivity before emitting env updates.
- `stripe setup` – provisioning for `starter` and `pro` plans, captures webhook + secret keys, can run headless with `--non-interactive`.
- `auth` – service-account token issuance, Ed25519 key rotation, JWKS printing (uses Vault transit when enabled).
- `infra` – wraps `make dev-*` and `make vault-*` plus dependency checks.
- `status` – manages `/api/v1/status` subscriptions/incidents.
- `config dump-schema` – audits every FastAPI setting with env alias, default, type, and wizard coverage.

Refer to `starter_cli/README.md` for detailed flags, answers-file formats, and contribution rules (imports must stay side-effect free; new env knobs require inventory + tracker updates).

## Development Workflow
- Keep FastAPI routers <300 lines; extract shared helpers once reused.
- Redis is dual-use: refresh-token cache and billing event transport. Coordinate settings through the wizard or `.env.local`.
- Secrets live in `var/keys/`; Vault workflows (`make vault-up`, `make verify-vault`) help issue signed tokens locally.
- Tests are SQLite + fakeredis by default (`conftest.py`); avoid leaking env mutations between tests.
- Backend edits → `hatch run lint` & `hatch run pyright`; frontend edits → `pnpm lint` & `pnpm type-check`.

## Key References
- `starter_cli/README.md` – CLI deep dive, command catalog.
- `SNAPSHOT.md` / `starter_cli/SNAPSHOT.md` – architecture overviews for the repo and CLI.
- `docs/openai-agents-sdk/` – SDK reference + integration patterns.
- `docs/frontend/data-access.md` & `docs/frontend/ui/components.md` – frontend architecture + component inventory.
- `docs/trackers/CLI_MILESTONE.md` – CLI roadmap and status.
- `Makefile` – curated commands for API, migrations, infra, Stripe tooling, and CLI invocation.

> Future sections can expand on backend internals, service boundaries, and frontend feature guides as they are reviewed. For now, use this README as the top-level map and follow the linked docs for deeper dives.
