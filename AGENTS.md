You are a professional engineer and developer in charge of the OpenAI Agent SaaS Starter Codebase. The OpenAI Agent SaaS Starter Codebase contains a Next.js 16 frontend and a FastAPI backend. The FastAPI backend is based on the latest new OpenAI Agents SDK (v0.6.4) and uses the brand new OpenAI models (gpt-5.1, gpt-5.2, and gpt-5-mini), each with reasoning capabilities (none|minimal|low|medium|high). 

# Overview
- This is a SaaS starter repo developers can easily clone and quickly set up their own AI Agent SaaS website. It is a pre-release (no data and not yet distributed) which you are responsible for getting production ready for release.

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

### Roles & RBAC (canonical)
- Source of truth: `docs/auth/roles.md`
- Tenant roles are `owner`, `admin`, `member`, `viewer` with ordered gates (member >= viewer).
- Platform role is separate (`platform_operator`) and stored on the user record.
- JWT `roles` claim is authoritative; scopes only infer a tenant role when `roles` is missing.
- `X-Tenant-Role` may only down-scope privileges.

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
- Declarative specs live in `api-service/src/app/workflows/**/spec.py`. You can define either a flat `steps` list or explicit `stages`.
- `WorkflowStage` supports `mode="sequential"` or `mode="parallel"` plus an optional `reducer` (`outputs, prior_steps -> next_input`) for fan-out/fan-in.
- `WorkflowStep` retains guard + input_mapper hooks and per-step `max_turns`. Registry validation ensures agent keys exist and, unless `allow_handoff_agents=True`, blocks handoff-enabled agents.
- Runner wraps executions in `agents.trace`, tags step records and SSE events with `stage_name` / `parallel_group` / `branch_index`, and uses reducers to merge parallel outputs before downstream stages.

### Agents vs Workflows (API service)
- `AgentSpec` (`api-service/src/app/agents/<key>/spec.py`) declares a single SDK agent: prompt/instructions, model selector, explicit tool surface, and optional handoff targets. Specs are loaded via `load_agent_specs()` and materialized into concrete OpenAI agents at startup.
- `WorkflowSpec` (`api-service/src/app/workflows/<name>/spec.py`) stitches existing agents into deterministic chains or fan-out/fan-in stages. It reuses agent prompts and only controls sequencing via guards, input mappers, and reducers; the workflow registry validates referenced agent keys.
- Reach for an agent spec when you need a single conversational entrypoint with tools or handoffs. Choose a workflow spec when you need a repeatable, auditable sequence where ordering and branching stay outside the model.

### Public SSE streaming contract (`public_sse_v1`)
- **Goal:** expose a stable, browser-safe SSE event stream for the web app while insulating it from raw provider event churn.
- **Inbound (provider → normalized):** OpenAI Agents SDK stream events are normalized into `AgentStreamEvent` (`apps/api-service/src/app/domain/ai/models.py`) by `OpenAIStreamingHandle` (`apps/api-service/src/app/infrastructure/providers/openai/streaming.py`).
- **Outbound (normalized → public):** `PublicStreamProjector` (`apps/api-service/src/app/api/v1/shared/public_stream_projector/projector.py`) projects internal events into the public contract `PublicSseEvent` (`apps/api-service/src/app/api/v1/shared/streaming.py`, `schema=public_sse_v1`).
- **Endpoints:** chat streaming (`apps/api-service/src/app/api/v1/chat/router.py`) and workflow run streaming (`apps/api-service/src/app/api/v1/workflows/router.py`) emit `data: <PublicSseEvent JSON>\n\n` frames and stop emitting after `kind=final|error`.
- **Contract docs + goldens:** the spec lives in `docs/contracts/public-sse-streaming/v1.md`; examples live in `docs/contracts/public-sse-streaming/examples/*.ndjson` and are enforced by `apps/api-service/tests/contract/streams/test_stream_goldens.py` (assertions in `apps/api-service/tests/utils/stream_assertions.py`).
- **Coverage tracking:** `docs/integrations/openai-responses-api/streaming-events/coverage-matrix.md` tracks raw provider events → public SSE events, usage, and fixture coverage.
- **When changing streaming:** update schema (`apps/api-service/src/app/api/v1/shared/streaming.py`) + projector(s) (`apps/api-service/src/app/api/v1/shared/public_stream_projector/**`), add/adjust a golden NDJSON fixture + assertions, then regenerate OpenAPI + TS client:
  - `cd packages/starter_console && starter-console api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures`
  - `cd apps/web-app && OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures`

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
  - `cd packages/starter_console && starter-console api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures` (paths are resolved from the repo root, so skip leading `../`)
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

## Console Charter – Starter Console (SC)
- **Purpose:** The SC is the single operator entrypoint for provisioning secrets, wiring third-party providers, generating env files for both the FastAPI backend and the Next.js frontend, and exporting audit artifacts. It uses the current Starter Console branding.
- **Boundaries:** SC never imports `api-service/src/app` modules directly. Shared logic (key generation, schema validation) must live in neutral `starter_contracts/*` modules to keep imports acyclic and to allow the console to run without initializing the server stack.
- **Execution modes:** Every workflow supports interactive prompts for first-time operators and headless execution via flags (`--non-interactive`, `--answers-file`, `--var`) so CI/CD can drive the same flows deterministically.
- **Testing contract:** Importing `starter-console` must be side-effect free (no DB/Vault connections). Unit tests stub network calls, and the repo-root `conftest.py` enforces SQLite/fakeredis overrides for all console modules.
- **Ownership & roadmap:** Platform Foundations owns the console. Work is tracked in `docs/trackers/CONSOLE_MILESTONE.md` with phases for rebrand, config extraction, adapter rewrites, hermetic testing, and CI guardrails. Any new console feature must update that tracker before merge.
- **Operator guide:** Day-to-day workflows and command references live in `starter_console/README.md`.
- **Python install standard (dev vs prod):**
  - Dev: run `just dev-install` once from repo root (performs `pip install -e packages/starter_contracts` and `pip install -e packages/starter_console`). Afterwards, use `starter-console …` from repo root—no `PYTHONPATH` or hatch required.
  - Prod/CI: build wheels and install non-editable (`pip wheel packages/starter_contracts packages/starter_console -w dist` then `pip install dist/starter_contracts-*.whl dist/starter_console-*.whl`).

# Development Guidelines
- You must maintain a professional clean architecture, referring to the documentations of the OpenAI Agents SDK and the `docs/openai-agents-sdk` and `docs/integrations/openai-responses-api` directories during development in order to ensure you abide by the latest API framework. 
- Avoid feature gates/flags and any backward compatibility changes - since our app is still unreleased
- **After Your Edits**
  - **Backend**: Run `hatch run lint` and `hatch run typecheck` (Pyright + Mypy) after all edits in backend; CI blocks merges on `hatch run typecheck`, so keep it green locally.
  - **Frontend**: Run `pnpm lint` and `pnpm type-check` after all edits in frontend to ensure there are no errors
  - **Console**: Run `cd packages/starter_console && hatch run lint` and `cd packages/starter_console && hatch run typecheck` after all console edits to keep the package green.
- When adding or changing API behavior, update both unit tests and the HTTP smoke suite in `apps/api-service/tests/smoke/http` (and keep `COVERAGE_MATRIX.md` aligned).
- Keep FastAPI routers roughly ≤300 lines by default—split files when workflows/dependencies diverge, but it’s acceptable for a single router to exceed that limit when it embeds tightly coupled security or validation helpers; extract those helpers into shared modules only once they are reused elsewhere.
- Avoid Pragmatic coupling
- Repo automation now lives in `justfile`; run `just help` to view tasks and prefer those recipes over ad-hoc commands. Use the Just recipes for infra + DB tasks (e.g., `just migrate`, `just start-backend`, `just test-unit`) instead of invoking alembic/uvicorn/pytest directly.
- Prior to developing complex features or significant refactors, create a `Milestone Tracker` based on the template in `docs/trackers/templates/MILESTONE_TEMPLATE.md`. A `Milestone Tracker` is the spec-and-execution doc for a deliverable slice of the project: it captures the goal, scope/guardrails, phased task breakdown with owners/status, and clear acceptance criteria/DoD. You use it as the single source of truth to implement and verify the work, and as the progress log to keep everyone aligned and prevent drift. Create active Milestone Trackers in `docs/trackers/current_milestones`. Once complete, they are archived in `docs/trackers/complete/{date}`.

## Pre-commit hooks (local)
- Install with `just pre-commit-install` (auto-installs `pre-commit` if missing).
- Hooks keep OpenAPI artifacts + web SDK in sync when API files change.
- Skip locally with `SKIP=openapi-export,web-sdk-generate git commit` (use sparingly).

# Test Environment Contract
- `conftest.py` at the repository root forces the entire pytest run onto SQLite + fakeredis and disables billing/auto migrations. **Do not** remove or bypass this file; any new package (console included) must behave correctly when those overrides are in effect.
- Run backend tests inside the hatch env (`cd apps/api-service && hatch run test …`) or `hatch shell`; invoking `pytest` with the host interpreter can miss dev extras like `fakeredis` even if they’re installed elsewhere.
- Any test that mutates `os.environ` must snapshot and restore the original values to avoid leaking state into other suites. Use the helpers in `api-service/tests/conftest.py` or mimic their pattern.
- When adding console modules, ensure module import has no side effects (e.g., avoid calling `get_settings()` or hitting the database at import time). If you need settings, fetch them inside the handler after env overrides have loaded.
- Postgres integration suites (`tests/integration/test_postgres_migrations.py`) remain skipped unless `USE_REAL_POSTGRES=true`; leave this off for local/unit CI runs so we never accidentally hit a developer's Postgres instance.

# Notes
- Throughout the codebase you will see SNAPSHOT.md files. These files contain architectural documentation using directory trees with inline comments to help you understand and navigate the project efficiently. They are not tracked in github.
    - Run `cb --snapshots` to idenitfy location of SNAPSHOT.md files.
    - Update snapshots by running `cb tree-sync-batch -y` to sync with the latest changes.
- Refer to `docs/trackers/` for the latest status of the codebase. Keep these trackers up to date with the latest changes and status of the codebase.
- When applying database migrations or generating new ones, always use the Just recipes (`just migrate`, `just migration-revision message="..."`) so your `apps/api-service/.env.local` secrets and `.env.compose` values are loaded consistently. These wrappers take care of wiring Alembic to the right Postgres instance (local Docker or remote) without manual exports.
- Need to test Vault Transit locally? Use `just vault-up` to start the dev signer, `just verify-vault` to run the console issuance smoke test, and `just vault-down` when you’re done. Details live in `docs/security/vault-transit-signing.md`.
- This repo hasn’t shipped a “stable” release yet, so we don’t carry any backward-compat baggage.
- When you come across a situation where you need the latest documentation, use your web search tool

## Local Logs (one place)
- All local logs live under `var/log/<YYYY-MM-DD>/` at the repo root (`var/log/current` points to today).
- Backend (FastAPI): `var/log/current/api/all.log` and `error.log` (requires `LOGGING_SINKS=file`, set in `apps/api-service/.env.local`).
- Frontend (Next dev): `var/log/current/frontend/all.log` and `error.log` via the bundled log tee used by `pnpm dev`.
- Console (CLI/TUI): `var/log/current/starter-console/all.log` and `error.log` when `CONSOLE_LOGGING_SINKS` includes `file` (default); Textual debug logs additionally write to `starter-console/textual.log` when `TEXTUAL_LOG` is set.
- Quick tail: `starter-console logs tail --service api --service frontend --service starter-console --errors`.

# Codebase Patterns
<patterns>
openai-agents-saas-starter/
├── apps/                         # Runtime apps (deployable services)
│   ├── api-service/              # FastAPI backend
│   │   ├── .artifacts/            # Generated artifacts (OpenAPI snapshots, fixtures)
│   │   ├── alembic/               # Database migrations
│   │   ├── src/app/               # Layered backend architecture
│   │   │   ├── api/               # FastAPI routing + API v1 modules/schemas
│   │   │   ├── agents/            # Agent specs/prompts + shared agent utilities
│   │   │   ├── guardrails/        # Guardrail checks + presets + shared guardrail plumbing
│   │   │   ├── workflows/         # Workflow specs + orchestration/runner logic
│   │   │   ├── domain/            # Domain models + ports (core business concepts)
│   │   │   ├── services/          # Application services / use-cases
│   │   │   ├── infrastructure/    # Persistence + integrations + repositories
│   │   │   ├── providers/         # External providers (OpenAI, secrets, storage, stripe, redis, etc.)
│   │   │   ├── observability/     # Logging/metrics/OTLP sinks + instrumentation
│   │   │   ├── middleware/        # Request/response middleware
│   │   │   └── core/ + bootstrap/ + utils/  # Settings, security, app wiring, helpers
│   │   ├── tests/                 # contract/, integration/, unit/, smoke/ (+ stream goldens/fixtures)
│   │   ├── scripts/               # One-off maintenance / admin scripts
│   │   ├── var/keys/              # Local signing keysets (Ed25519)
│   │   └── justfile               # App-scoped tasks (pairs with root justfile)
│   └── web-app/                   # Next.js App Router frontend
│       ├── app/                   # Route groups: (marketing)/, (auth)/, (app)/(workspace)
│       │   └── api/               # BFF/edge route handlers (proxy to backend, streaming, downloads)
│       ├── features/              # Feature modules (chat, agents, billing, settings, etc.)
│       ├── components/            # shadcn/ui + shared UI assemblies
│       ├── lib/                   # API client, server helpers, streaming utilities
│       │   └── api/client/        # Generated OpenAPI TS client + types (*.gen.ts)
│       ├── hooks/                 # Shared React hooks
│       ├── tests/                 # Playwright e2e + Vitest unit tests
│       ├── .storybook/            # Storybook config + mocks/fixtures
│       ├── seeds/                 # Test seeds/config (e.g., Playwright)
│       ├── public/                # Static assets
│       └── justfile               # App-scoped tasks
├── packages/                      # Shared Python libraries (reused across apps)
│   ├── starter_console/               # Operator console (Typer/Rich TUI, setup wizard, probes, tests)
│   │   └── justfile               # Package-scoped tasks
│   ├── starter_contracts/         # Shared contracts/models/config used by console + backend (tests, py.typed)
│   └── starter_providers/         # Cloud provider SDK helpers shared across the backend and the Starter Console.
├── ops/                           # Local infra configs
│   ├── compose/                   # Docker compose stacks (vault/minio/etc.)
│   └── observability/             # Collector/config generation helpers
├── tools/                         # Repo tooling (typecheck, smoke tests, vault helpers, module viz)
├── scripts/                       # Repo-level helper scripts (e.g., vault file/log helpers)
├── var/                           # Local runtime outputs (keys/, observability/, ...)
├── .env.compose*                  # Repo-level dev env for compose (example + real)
├── .nvmrc                         # Node version pin for JS tooling
├── justfile                       # Root task runner (preferred entrypoint; complements per-app justfiles)
├── package.json                   # Workspace root for JS/TS tooling
├── pnpm-workspace.yaml            # pnpm workspace definition
└── tsconfig.scripts.json          # TS config for repo-level scripts beside each app/package
</patterns>
