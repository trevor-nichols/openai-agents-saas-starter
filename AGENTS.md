You are a professional engineer and developer in charge of the OpenAI Agent Starter Codebase. The OpenAI Agent Starter Codebase contains a Next.js 16 frontend and a FastAPI backend. The FastAPI backend is based on the latest new OpenAI Agents SDK (v0.6.1) and uses the brand new GPT-5.1 model with reasoning. 

# Overview
- This is a SaaS starter repo developers can easily clone and quickly set up their own AI Agent SaaS website. It is a pre-release (no data this and has not been distributed) which you are responsible for getting production ready for release.

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

### Alembic / database hygiene (dev)
- We carry two migration heads (activity + workflow). Always run `just migrate` or let `AUTO_RUN_MIGRATIONS=true` handle it—both now call `alembic upgrade heads` (plural). Avoid `upgrade head` or targeting a single branch.
- Never truncate or hand-edit `alembic_version`. If you need to align an existing schema without data loss, use `alembic stamp heads`; if data is disposable, drop + recreate the DB then rerun `just migrate`.
- Don’t manually create tables; schema drift without matching `alembic_version` rows leads to “relation already exists” / startup hangs.
- New migrations that depend on other branches must declare `depends_on` to enforce ordering (see `b6dcb157d208` depending on `c3c9b1f4cf29`).
- Migration policy (autogen by default; manual needs approval):
  - Default: `just migration-revision message="add widget table"` (wraps `alembic revision --autogenerate ...`). Review the generated file before committing.
  - Apply: `just migrate` (runs `scripts/check_alembic_version.py` first, then `alembic upgrade heads`).
  - Manual revisions are forbidden unless a lead explicitly approves a one-off (e.g., irreconcilable autogen). If approved, run inside `apps/api-service`: `hatch run alembic revision -m "manual step"` and follow with a merge revision if multiple heads arise.
  - Never bypass `just migrate` or edit `alembic_version` directly; fix multi-heads with merge revisions, not deletes.

### Workflow orchestration (API service)
- Declarative specs live in `api-service/src/app/workflows/**/spec.py`. You can define either a flat `steps` list (legacy) or explicit `stages`.
- `WorkflowStage` supports `mode="sequential"` or `mode="parallel"` plus an optional `reducer` (`outputs, prior_steps -> next_input`) for fan-out/fan-in.
- `WorkflowStep` retains guard + input_mapper hooks and per-step `max_turns`. Registry validation ensures agent keys exist and, unless `allow_handoff_agents=True`, blocks handoff-enabled agents.
- Runner wraps executions in `agents.trace`, tags step records and SSE events with `stage_name` / `parallel_group` / `branch_index`, and uses reducers to merge parallel outputs before downstream stages.

### Agents vs Workflows (API service)
- `AgentSpec` (`api-service/src/app/agents/<key>/spec.py`) declares a single SDK agent: prompt/instructions, model selector, explicit tool surface, and optional handoff targets. Specs are loaded via `load_agent_specs()` and materialized into concrete OpenAI agents at startup.
- `WorkflowSpec` (`api-service/src/app/workflows/<name>/spec.py`) stitches existing agents into deterministic chains or fan-out/fan-in stages. It reuses agent prompts and only controls sequencing via guards, input mappers, and reducers; the workflow registry validates referenced agent keys.
- Reach for an agent spec when you need a single conversational entrypoint with tools or handoffs. Choose a workflow spec when you need a repeatable, auditable sequence where ordering and branching stay outside the model.

## Frontend
- The frontend uses the HeyAPI SDK to generate the API client. The API client is generated into the `lib/api/client` directory.
- All hooks use TanStack Query
- Use Shadcn components from components/ui/. DO NOT create custom components. If a component we need is not included yet, add it. Refer to `docs/frontend/ui/components.md` for the latest list of components.
- Detailed frontend data-access patterns (SDK → services → API routes → hooks) live in `docs/frontend/data-access.md`. Review that doc before adding new queries or routes.
- Browser-facing code must NOT call the FastAPI backend directly. Always route through Next.js API routes that attach auth from cookies. In `lib/api/**` use fetches to `/api/...` proxy routes; direct SDK calls are allowed only in server-only utilities that already use `getServerApiClient()`.
- Separation of Concerns
  - lib/queries/ = Server data (TanStack Query)
  - hooks/ = UI logic, local state, browser APIs

### OpenAPI + SDK regeneration
- Export superset schema (billing + test fixtures) from repo root:
  - `cd packages/starter_cli && python -m starter_cli.app api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures` (paths are resolved from the repo root, so skip leading `../`)
- Regenerate the frontend client offline using that artifact:
  - `cd apps/web-app && OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures`
  - Output is written to `apps/web-app/lib/api/client/`.
- **Hard rule:** Any API/schemas change (backend or contracts) must run the two commands above *before* touching web-app code. Do not hand-edit generated SDK files. Frontend edits that depend on new fields should be in the same PR *after* regeneration.

### Next.js 16 working notes (must-read for frontend)
- Toolchain: Node 20.9+ (we pin .nvmrc to 22), TypeScript 5.1+, React 19.2, Next 16.0.3; Turbopack is default for dev/build (no need for `--turbopack`; opt out with `--webpack` only if required).
- Routing/runtime APIs are async-only: `cookies()`, `headers()`, `draftMode()`, `params`, `searchParams`, metadata image params/id, and sitemap `id` must be awaited inside async components. Use `PageProps`/`LayoutProps` from `next typegen` for typing.
- `middleware` is renamed to `proxy` (Node runtime only). File is `proxy.ts` with a `proxy` export; `skipMiddlewareUrlNormalize` becomes `skipProxyUrlNormalize`.
- Cache model: PPR flags are removed; opt into Cache Components via `cacheComponents` in `next.config.ts`. Keep runtime data (cookies/headers/searchParams) outside cached scopes or wrap the dynamic parts in `<Suspense>`; use `'use cache'` + `cacheLife/cacheTag` only for data that is safe to cache.
- Parallel routes require explicit `default.tsx` per slot (return `null` or `notFound()`).
- Images: local src with query strings need `images.localPatterns.search`; defaults changed (`minimumCacheTTL` 4h, `qualities` [75], `imageSizes` drops 16px, `maximumRedirects`=3). Prefer `remotePatterns` over deprecated `images.domains`.
- Removed/renamed: `next lint`, `serverRuntimeConfig/publicRuntimeConfig`, `experimental.ppr/dynamicIO/turbopack`, `unstable_rootParams`, `next/legacy/image`. Use env vars (`NEXT_PUBLIC_*`) plus `connection()` when values must be read at runtime.
- Behavior changes: `scroll-behavior` no longer overridden—add `data-scroll-behavior="smooth"` on `<html>` if you want the old smooth-scroll reset; dev output now lives in `.next/dev` (update scripts that inspect build artifacts).

### Frontend Component Architecture Pattern

- **Feature-centric directories** live under `features/<domain>/` (e.g., `features/chat`, `features/billing`, `features/account`). Each exports a single orchestrator consumed by the page.
- **Directory shape per feature:**

  ```
  features/chat/
    index.ts              // public exports for the feature
    ChatWorkspace.tsx     // orchestrator/container (client component)
    components/
      MessageList.tsx
      MessageInput.tsx
      ConversationHeader.tsx
      index.ts
    constants.ts          // copy, layout config, status labels
    types.ts              // view-specific types (domain types remain in /types)
    hooks/
      useMessageFocus.ts  // purely view-level composition
      index.ts
    utils/
      formatMessage.ts    // pure helpers scoped to this feature
  ```

- **Pages stay lean:** `app/.../page.tsx` imports the feature orchestrator and handles only layout/metadata. Shared chrome for a route group belongs in `_components/` next to the layout, while the feature content stays within `features/**`.
- **Route chrome vs. shared UI:** For marketing, keep persistent chrome (header, footer, nav, layout scaffolding) in `app/(marketing)/_components/`. Place marketing-specific sections reusable across pages in `features/marketing/components/`. Put cross-app primitives (buttons, banners, cards) in `components/ui/` so they remain Shadcn-style and domain agnostic.
- **Data layer remains centralized:** Continue using `lib/api`, `lib/queries`, `lib/chat`, and `/types` for network/data contracts. Feature hooks only compose those primitives; anything broadly useful graduates to `components/ui/` or `components/shared/`.
- **Ownership split:** Engineering owns the shared hooks/services in `lib/**`; the design/UI team iterates inside `features/<domain>/components` using those hooks. Any new cross-feature logic graduates back into `lib/**` so other surfaces stay consistent.
- **Testing:** Colocate unit/interaction tests with the orchestrator (`ChatWorkspace.test.tsx`). Promote reusable test helpers to existing shared testing utilities when multiple features need them.

### Component placement guide (UI vs feature vs route chrome)
- `components/ui/` – domain-agnostic primitives and small families (e.g., buttons, inputs, tooltip, marquee, motion wrappers, avatar, hero variants, code-block). Use lowercase dirs, PascalCase files, and a barrel `index.ts` per folder.
- `features/<domain>/components/` – domain/workflow compositions that stitch data + UI (e.g., chat transcript drawer, billing panels). Reused across pages within that domain.
- `app/(group)/_components/` – route-group chrome/layout (e.g., marketing header/footer, auth card). Keep close to the pages they serve.
- Rule of thumb: generic everywhere → `ui`; cross-page domain → `features`; single route-group shell → `app/(group)/_components`.

## CLI Charter – Starter CLI (SC)
- **Purpose:** The SC is the single operator entrypoint for provisioning secrets, wiring third-party providers, generating env files for both the FastAPI backend and the Next.js frontend, and exporting audit artifacts. It replaces the legacy branding from earlier iterations.
- **Boundaries:** SC never imports `api-service/src/app` modules directly. Shared logic (key generation, schema validation) must live in neutral `starter_contracts/*` modules to keep imports acyclic and to allow the CLI to run without initializing the server stack.
- **Execution modes:** Every workflow supports interactive prompts for first-time operators and headless execution via flags (`--non-interactive`, `--answers-file`, `--var`) so CI/CD can drive the same flows deterministically.
- **Testing contract:** Importing `python -m starter_cli.app` must be side-effect free (no DB/Vault connections). Unit tests stub network calls, and the repo-root `conftest.py` enforces SQLite/fakeredis overrides for all CLI modules.
- **Ownership & roadmap:** Platform Foundations owns the CLI. Work is tracked in `docs/trackers/CLI_MILESTONE.md` with phases for rebrand, config extraction, adapter rewrites, hermetic testing, and CI guardrails. Any new CLI feature must update that tracker before merge.
- **Operator guide:** Day-to-day workflows and command references live in `starter_cli/README.md`.
- **Python install standard (dev vs prod):**
  - Dev: run `just dev-install` once from repo root (performs `pip install -e packages/starter_contracts` and `pip install -e packages/starter_cli`). Afterwards, use `python -m starter_cli.app …` from repo root—no `PYTHONPATH` or hatch required.
  - Prod/CI: build wheels and install non-editable (`pip wheel packages/starter_contracts packages/starter_cli -w dist` then `pip install dist/starter_contracts-*.whl dist/starter_cli-*.whl`).

# Development Guidelines
- You must maintain a professional clean architecture, referring to the documentations of the OpenAI Agents SDK and the `docs/openai-agents-sdk` directory whenever needed in order to ensure you abide by the latest API framework. 
- Avoid feature gates/flags and any backwards compability changes - since our app is still unreleased
- **After Your Edits**
  - **Backend**: Run `hatch run lint` and `hatch run typecheck` (Pyright + Mypy) after all edits in backend; CI blocks merges on `hatch run typecheck`, so keep it green locally.
  - **Fronted**: Run `pnpm lint` and `pnpm type-check` after all edits in frontend to ensure there are no errors
- Keep FastAPI routers roughly ≤300 lines by default—split files when workflows/dependencies diverge, but it’s acceptable for a single router to exceed that limit when it embeds tightly coupled security or validation helpers; extract those helpers into shared modules only once they are reused elsewhere.
- Avoid Pragmatic coupling
- Repo automation now lives in `justfile`; run `just help` to view tasks and prefer those recipes over ad-hoc commands. Use the Just recipes for infra + DB tasks (e.g., `just migrate`, `just start-backend`, `just test-unit`) instead of invoking alembic/uvicorn/pytest directly.

# Test Environment Contract
- `conftest.py` at the repository root forces the entire pytest run onto SQLite + fakeredis and disables billing/auto migrations. **Do not** remove or bypass this file; any new package (CLI included) must behave correctly when those overrides are in effect.
- Run backend tests inside the hatch env (`cd apps/api-service && hatch run pytest …`) or `hatch shell`; invoking `pytest` with the host interpreter can miss dev extras like `fakeredis` even if they’re installed elsewhere.
- Any test that mutates `os.environ` must snapshot and restore the original values to avoid leaking state into other suites. Use the helpers in `api-service/tests/conftest.py` or mimic their pattern.
- When adding CLI modules, ensure module import has no side effects (e.g., avoid calling `get_settings()` or hitting the database at import time). If you need settings, fetch them inside the handler after env overrides have loaded.
- Postgres integration suites (`tests/integration/test_postgres_migrations.py`) remain skipped unless `USE_REAL_POSTGRES=true`; leave this off for local/unit CI runs so we never accidentally hit a developer's Postgres instance.

# Notes
- Throughout the codebase you will see SNAPSHOT.md files. These files contain architectural documentation using directory trees with inline comments to help you understand and navigate the project efficiently. You can update these by running `cb tree-sync /path/to/directory --snapshot SNAPSHOT.md --yes` (outside of .venv) to sync the tree with the latest changes.
- Refer to `docs/trackers/` for the latest status of the codebase. Keep these trackers up to date with the latest changes and status of the codebase.
- When applying database migrations or generating new ones, always use the Just recipes (`just migrate`, `just migration-revision message="..."`) so your `apps/api-service/.env.local` secrets and `.env.compose` values are loaded consistently. These wrappers take care of wiring Alembic to the right Postgres instance (local Docker or remote) without manual exports.
- Need to test Vault Transit locally? Use `just vault-up` to start the dev signer, `just verify-vault` to run the CLI issuance smoke test, and `just vault-down` when you’re done. Details live in `docs/security/vault-transit-signing.md`.
- Thishe repo hasn’t shipped a “stable” release yet, so we don’t carry any backward-compat baggage.
- When you come across a situation where you need the latest documentation, use your web search tool

## Local Logs (one place)
- All local logs live under `var/log/<YYYY-MM-DD>/` at the repo root (`var/log/current` points to today).
- Backend (FastAPI): `var/log/current/api/all.log` and `error.log` (requires `LOGGING_SINK=file`, set in `apps/api-service/.env.local`).
- Frontend (Next dev): `var/log/current/frontend/all.log` and `error.log` via the bundled log tee used by `pnpm dev`.
- CLI (detached runs): `var/log/current/cli/*.log` per process when started with `just start-dev -- --detached`.
- Quick tail: `python -m starter_cli.app logs tail --service api --service frontend --errors`.

# Codebase Patterns
openai-agents-saas-starter/
├── apps/                         # Runtime apps
│   ├── api-service/              # FastAPI backend (see apps/api-service/SNAPSHOT.md)
│   │   ├── alembic/              # Database migrations
│   │   ├── src/app/              # Agents, API v1, services, infrastructure, workflows
│   │   ├── tests/                # contract/, integration/, unit/ suites
│   │   └── var/keys/             # Ed25519 signing keys
│   └── web-app/                  # Next.js 16 frontend (see apps/web-app/SNAPSHOT.md)
│       ├── app/                  # App Router groups: marketing, auth, app/workspace
│       ├── features/             # Feature orchestrators (chat, billing, account, etc.)
│       ├── components/           # Shadcn UI + domain assemblies
│       ├── lib/                  # API client, config, streaming helpers
│       ├── hooks/                # Client-side hooks
│       ├── tests/ + storybook    # Vitest/Playwright and Storybook assets
│       └── public/               # Static assets
├── packages/                     # Shared Python libraries
│   ├── starter_cli/              # Operator CLI (src/starter_cli/, tests/, justfile)
│   └── starter_contracts/        # Shared contracts used by CLI + backend
├── tools/                        # CI/utility scripts (typecheck, smoke tests, vault helpers)
├── ops/                          # Local infra configs (compose stacks, observability)
├── docs/                         # SDK reference, trackers, frontend docs
├── scripts/                      # Repo-level helper scripts
├── var/                          # Local runtime data (keys/, log/, reports/)
├── justfile                      # Top-level task runner (preferred over ad-hoc commands)
├── package.json / pnpm-workspace.yaml # Workspace root for JS/TS tooling
├── tsconfig.scripts.json         # TS config for repo scripts
└── SNAPSHOT.md                   # Root structure reference; per-project snapshots live beside each app/package
