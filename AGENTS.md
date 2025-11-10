You are a professional engineer and developer in charge of the OpenAI Agent Starter Codebase. The OpenAI Agent Starter Codebase contains a Next.js frontend and a FastAPI backend. The FastAPI backend is based on the latest new OpenAI Agents SDK (v0.5.0)and uses the brand new GPT-5 model with reasoning. 

# Overview
- This is a SaaS starter repo people can easily clone and quickly set up their own AI Agent SaaS website

## Backend
- Request auth funnels through FastAPI dependencies into JWT-backed services
- Persistence is Postgres via repository interfaces plus Redis caches
- Alembic manages migrations
- Async SQLAlchemy engine
- Repository implementations are Postgres-first across auth, billing, conversations, Stripe events, and shared base models
- Redis shows up twice: as the refresh-token cache and as the transport for billing event streams 
- FastAPI dependency modules gate protected routes with helpers like require_current_user, so every router can require an authenticated human or service account before hitting business logic.
- Keys are Ed25519 
- Long-lived secrets such as signing keys live under var/keys/

## Frontend
- The frontend uses the HeyAPI SDK to generate the API client. The API client is generated into the `lib/api/client` directory.
- All hooks use TanStack Query

## CLI Charter – Starter CLI (SC)
- **Purpose:** The SC is the single operator entrypoint for provisioning secrets, wiring third-party providers, generating env files for both the FastAPI backend and the Next.js frontend, and exporting audit artifacts. It replaces the legacy “Anything Agents” branding.
- **Boundaries:** SC never imports `anything-agents/app` modules directly. Shared logic (key generation, schema validation) must live in neutral `starter_shared/*` modules to keep imports acyclic and to allow the CLI to run without initializing the server stack.
- **Execution modes:** Every workflow supports interactive prompts for first-time operators and headless execution via flags (`--non-interactive`, `--answers-file`, `--var`) so CI/CD can drive the same flows deterministically.
- **Testing contract:** Importing `python -m starter_cli.cli` must be side-effect free (no DB/Vault connections). Unit tests stub network calls, and the repo-root `conftest.py` enforces SQLite/fakeredis overrides for all CLI modules.
- **Ownership & roadmap:** Platform Foundations owns the CLI. Work is tracked in `docs/trackers/CLI_MILESTONE.md` with phases for rebrand, config extraction, adapter rewrites, hermetic testing, and CI guardrails. Any new CLI feature must update that tracker before merge.

# Development Guidelines
- You must maintain a professional clean architecture, referring to the documentations of the OpenAI Agents SDK and the `docs/openai-agents-sdk` directory whenever needed in order to ensure you abide by the latest API framework. 
- Avoid feature gates/flags and any backwards compability changes - since our app is still unreleased
- **Backend**: Run `hatch run lint` and `hatch run pyright` after all edits to ensure there are no errors
- Keep FastAPI routers roughly ≤300 lines by default—split files when workflows/dependencies diverge, but it’s acceptable for a single router to exceed that limit when it embeds tightly coupled security or validation helpers; extract those helpers into shared modules only once they are reused elsewhere.

# Test Environment Contract
- `conftest.py` at the repository root forces the entire pytest run onto SQLite + fakeredis and disables billing/auto migrations. **Do not** remove or bypass this file; any new package (CLI included) must behave correctly when those overrides are in effect.
- Any test that mutates `os.environ` must snapshot and restore the original values to avoid leaking state into other suites. Use the helpers in `anything-agents/tests/conftest.py` or mimic their pattern.
- When adding CLI modules, ensure module import has no side effects (e.g., avoid calling `get_settings()` or hitting the database at import time). If you need settings, fetch them inside the handler after env overrides have loaded.
- Postgres integration suites (`tests/integration/test_postgres_migrations.py`) remain skipped unless `USE_REAL_POSTGRES=true`; leave this off for local/unit CI runs so we never accidentally hit a developer's Postgres instance.

# Notes
- Throughout the codebase, you will see `SNAPSHOT.md` files. `SNAPSHOT.md` files contain the full structure of the codebase at a given point in time. Refer to these files when you need understand the architecture or need help navigating the codebase.
- Refer to `docs/trackers/` for the latest status of the codebase. Keep these trackers up to date with the latest changes and status of the codebase.
- When applying database migrations or generating new ones, always use the Makefile targets (`make migrate`, `make migration-revision`) so your `.env.local`/`.env` secrets and `.env.compose` values are loaded consistently. These wrappers take care of wiring Alembic to the right Postgres instance (local Docker or remote) without manual exports.

# Codebase Patterns
openai-agents-starter/
├── pyproject.toml
├── agent-next-15-frontend/
│   ├── app/
│   │   ├── (agent)/
│   │   │   ├── actions.ts
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── globals.css
│   │   └── layout.tsx
│   ├── components/
│   │   └── agent/
│   │       ├── ChatInterface.tsx
│   │       └── ConversationSidebar.tsx
│   ├── hooks/
│   │   └── useConversations.ts
│   ├── lib/
│   │   └── api/
│   │       ├── client/… (generated HeyAPI SDK)
│   │       ├── config.ts
│   │       └── streaming.ts
│   ├── types/
│   │   └── generated/… (OpenAPI types)
│   └── config + tooling files (package.json, tailwind.config.ts, etc.)
├── anything-agents/
│   ├── alembic/ (database migrations)
│   ├── app/
│   │   ├── api/ (FastAPI layer - versioned routes, dependencies, models)
│   │   │   ├── dependencies/ (auth, tenant, common)
│   │   │   ├── models/ (Pydantic request/response schemas)
│   │   │   └── v1/ (agents, auth, billing, chat, conversations, tools)
│   │   ├── cli/ (command-line tools for auth management)
│   │   ├── core/ (config, security, keys, service accounts)
│   │   ├── domain/ (business models, repository protocols)
│   │   │   ├── auth.py, billing.py, conversations.py, users.py
│   │   ├── infrastructure/ (external integrations)
│   │   │   ├── db/ (SQLAlchemy engine, sessions)
│   │   │   ├── openai/ (Agents SDK wrappers)
│   │   │   ├── persistence/ (repository implementations)
│   │   │   │   ├── auth/, billing/, conversations/, stripe/
│   │   │   ├── security/ (nonce store, Vault clients)
│   │   │   └── stripe/ (Stripe API client)
│   │   ├── middleware/ (logging with correlation IDs)
│   │   ├── observability/ (structured logging, Prometheus metrics)
│   │   ├── presentation/ (health checks, webhooks, well-known endpoints)
│   │   ├── services/ (orchestration layer)
│   │   │   ├── agent_service.py, auth_service.py
│   │   │   ├── billing_service.py, billing_events.py
│   │   │   ├── conversation_service.py, user_service.py
│   │   │   ├── payment_gateway.py, stripe_dispatcher.py, stripe_retry_worker.py
│   │   └── utils/
│   │       └── tools/ (agent tool registry and definitions)
│   ├── main.py (FastAPI application entry point)
│   ├── tests/
│   │   ├── contract/ (API endpoint contract tests)
│   │   ├── integration/ (tests with real database/Redis)
│   │   ├── unit/ (fast tests with mocks)
│   │   ├── fixtures/ (test data: keysets, Stripe events)
│   │   └── utils/ (test helpers)
│   └── var/keys/ (Ed25519 signing keys)
└── docs/
    ├── openai-agents-sdk/ (SDK reference documentation)
    │   ├── agents/, examples/, tracing/, memory/, handoffs/, etc.
    └── trackers/ (development status tracking)
