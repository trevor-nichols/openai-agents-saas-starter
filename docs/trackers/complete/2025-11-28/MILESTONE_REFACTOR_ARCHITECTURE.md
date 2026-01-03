# Milestone: Repository Architecture Refactor (Apps/Packages Mono)

Status: Phase 5 complete (validation green); rollout tasks pending (Phase 6)
Owner: Platform Foundations
Goal: Present a professional, extensible mono-repo layout with clear app/package boundaries, predictable tooling, and onboarding-ready docs.

## Target Layout (desired end state)

```
justfile                # root orchestrator; delegates to package justfiles
ops/compose/…           # infra docker-compose + observability generator (stays)
docs/                   # product + engineering docs, trackers
apps/
  api-service/          # FastAPI service (Agents SDK)
  web-app/              # Next.js 16 frontend
packages/
  starter_console/          # operator CLI
  starter_contracts/    # shared contracts/lib
tools/                  # shared scripts (smoke tests, moduleviz, vault helpers, env inventory)
var/                    # runtime artifacts (keys, logs, reports) – gitignored, documented
.env.local(.example) -> apps/api-service/.env.local(.example)
.env.compose(.example)
pnpm-workspace.yaml     # spans apps/* and packages/* JS/TS workspaces
tsconfig.scripts.json   # shared TS config for tools/scripts
.github/                # CI, issue templates
```

Principles: keep apps isolated, shared code only via packages/, avoid path hacks, preserve just-based workflows, document runtime state under var/, and leave room for additional packages without reworking infra.

## Phases

### Phase 0 — Discovery & guardrails - s/o: *codex* 11/28/2025

What was done
- Walked all SNAPSHOT.md files (root, api-service, web-app, starter_console, starter_contracts, scripts, ops) and the live tree to spot stray artifacts and path assumptions.
- Reviewed env files + gitignore coverage for runtime state and generated assets.
- Collected path-sensitive tooling that will break when directories move.

Inventory highlights
- Root still owns (post-move snapshot): `apps/api-service/`, `apps/web-app/`, `packages/starter_console/`, `packages/starter_contracts/`, `scripts/`, `ops/`, `var/`, `.env.compose`, `pnpm-workspace.yaml`, `tsconfig.scripts.json`, `justfile`, node_modules/.venv (gitignored). No nested `api-service/api-service` folder exists; only `api-service/.artifacts` is present.
- `var/` contains `keys/`, `log/`, `logs/`, `reports/`; fully gitignored (note: var/ blanket ignore will hide future runtime assets unless explicitly surfaced).
- Ops: compose files live at `ops/compose/*.yml`; observability generator at `ops/observability/render_collector_config.py` used by just recipes.

Env + gitignore posture
- Env files: `apps/api-service/.env.local`, `apps/api-service/.env.example`, `.env.compose`, `.env.compose.example`; all gitignored alongside generic `.env*` variants.
- `var/` is globally ignored; caches (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `.next`) are already covered. Keeping env + var at root is compatible with the target layout; future `apps/*` and `packages/*` need no gitignore changes unless we add new build dirs.

Path-sensitive tooling (must update in Phases 2–3)
- `justfile` delegates: `api_just := "just -f api-service/justfile"`, `cli_just := "just -f starter_console/justfile"`, `contracts_just := "just -f starter_contracts/justfile"`, `web_just := "just -f web-app/justfile"`; compose_file paths assume `ops/compose/...` from repo root.
- Python type runner `scripts/typecheck.py` hardcodes `api-service/…`, `starter_console/…`, `starter_contracts/…` paths.
- Sys.path injections targeting `api-service`: `starter_console/src/starter_console/__init__.py`; CLI commands (`commands/api.py`), workflows (`workflows/setup/demo_token.py`, `workflows/setup/dev_user.py`); smoke + CI scripts (`scripts/check_secrets.py`, `scripts/smoke/platform_smoke.py`); Alembic/env bootstrap (`api-service/alembic/env.py`, `api-service/src/run.py`).
- JS/TS workspace: `pnpm-workspace.yaml` includes only `web-app`; Storybook/configs and package.json scripts assume `web-app` at repo root.
- Docs with hard-coded paths: `docs/CONTRACTS.md` (api-service sys.path mention) and README repo-structure section (will need refresh post-move).

Risk log (pre-move)
- Sys.path shims will fail once `api-service` relocates → plan: central helper for backend path, update all references in one pass during Phase 3.
- `scripts/typecheck.py` and CI/workflow globs will skip packages after relocation → update paths + CI configs concurrently with the move.
- `pnpm-workspace.yaml` currently excludes any future TS packages under packages/ → must expand to `apps/*` + `packages/*` when moving web-app.
- Blanket `var/` ignore can hide newly structured runtime outputs (e.g., tools/ artifacts) → add per-subdir README and selective allowlists in later phase.

Dependency map (current state)
- `starter_console` → imports backend modules via sys.path injection; also shells to `ops/compose` and reads root `.env*` through `env_runner` in justfile.
- `scripts/` → backend-dependent helpers (`check_secrets.py`, smoke tests) expect `api-service` relative to repo root.
- `web-app` → depends on generated HeyAPI client at `web-app/lib/api/client/`; codegen instructions reference `api-service/.artifacts/openapi-*.json` from repo root.
- `starter_contracts` → shared dependency for backend and CLI; guard tests enforce no reverse imports.
- `ops/compose` → invoked from root just tasks; path will change if justfile not updated post-move.

Feed-into next phases
- Prepare a path constants helper for Python scripts to avoid repeating relative math when we relocate.
- Update repo structure docs + README in Phase 1 with clarified ownership and var/ policy.

### Phase 1 — Layout contract & docs - s/o: *codex* 11/28/2025
- Added `docs/architecture/repo-layout.md` with target tree, ownership/boundaries, dependency rules, runtime state policy for `var/`, and guidance for adding new apps/packages/tools.
- Documented naming conventions and disallowed import edges (apps↔packages/tools) plus path conventions to update during relocation.
- Updated README with “Repo Layout (target for refactor milestone)” section and link back to the layout contract so newcomers see the planned structure before the move.

### Phase 2 — Filesystem reshuffle - s/o: *codex* 11/28/2025
- Scope (planned): move backend/frontend/CLI/contracts into `apps/` + `packages/`, create `tools/` for shared scripts, keep `ops/` + `var/` stable.
- Completed moves: `api-service` → `apps/api-service`, `web-app` → `apps/web-app`, `starter_console` → `packages/starter_console`, `starter_contracts` → `packages/starter_contracts`, and all former `scripts/` utilities into `tools/` (moduleviz, smoke, assert-billing, vault helpers, typecheck, check_secrets).
- Updated orchestration/tooling: root `justfile` delegates + CLI runners repointed; `tools/typecheck.py`, `pnpm-workspace.yaml` (apps/*, packages/*), `tsconfig.scripts.json` include path, compose vault volume, and package.json stripe script updated.
- Refreshed path-sensitive utilities: CLI sys.path shims/workflows point to `apps/api-service`; smoke/check_secrets/moduleviz/assert-billing adjusted; CI workflows (backend + frontend) and compose mounts updated; vault compose now mounts `tools/vault`.
- Docs/front-door touchups: README + AGENTS commands reflect new locations; `docs/CONTRACTS` and starter-console README updated for tools/ + `apps/api-service` paths.
- Follow-ups: sweep remaining doc references to prior `scripts/` and root-level `starter-console` invocations (many trackers/runbooks) or add a transition shim; regenerate SNAPSHOTs after phase 3.
- Aggregate quality gates added at root (`just lint-all`, `just typecheck-all`). All lint/typecheck suites now passing after path fixes; API service justfile env_runner repointed to `packages/starter_console`.

### Phase 3 — Tooling & config updates
### Phase 3 — Tooling & config updates - s/o: *codex* 11/28/2025
- Root `justfile` delegates updated; added `lint-all` / `typecheck-all`; api-service env_runner now points to `packages/starter_console`.
- Type/lint runners adjusted (`tools/typecheck.py`), pyright/mypy paths fixed; api-service pyproject/pyrightconfig now resolve `../../packages/starter_contracts`.
- CI workflows repointed (backend/frontend) and compose vault mount fixed; pnpm install run under `apps/web-app` after move.
- Docs/trackers cleaned of prior `scripts/` references in issue tracker and service architecture notes.
- Lint/typecheck suites run and green across backend/CLI/contracts/web.

### Phase 4 — Code imports & runtime wiring - s/o: *codex* 11/28/2025
- Sweep for relative path assumptions in Python (alembic env.py, tests, fixtures) and rewrite to use package-relative imports that remain valid after the move.
- Update frontend codegen paths (HeyAPI output, generated types) if any scripts assume `web-app/lib/api/client`; verify codegen commands in docs still work from new cwd.
- Verify CLI commands that shell out to `ops/compose` or expect `.env*` at root still resolve correctly after directory depth changes.
- Ensure `starter_console` and `api-service` continue to share contracts only via `starter_contracts` package (no cross-imports through sys.path).

### Phase 5 — Validation & developer experience - s/o: *codex* 11/29/2025
- Snapshots left to the user (per request); no regeneration in this phase.
- Full quality gates run in new layout: `just lint-all`, `just typecheck-all`, `just backend-test`, `just cli-test`, `just contracts-test`, `just web-test`, plus `python tools/smoke/platform_smoke.py` (all green).
- Starter Console tests now hermetic after storage section addition and env isolation; added prompt_choice support, storage defaults, and regenerated `docs/trackers/CONSOLE_ENV_INVENTORY.md`.
- Onboarding/docs refreshed via the layout contract + regenerated env inventory; repo-wide type checks anchored to `tools/typecheck.py` and Just targets.
- Added migration notes/faq touches in ISSUE_TRACKER.md and ensured path-sensitive tooling honors `apps/` / `packages/` structure.

### Phase 6 — Rollout & follow-ups
- Cut a short-lived `refactor/layout` branch with a migration guide; ensure CI passes there before merging to main.
- After merge, clean stale caches/artifacts (`.ruff_cache`, `.mypy_cache`, `.next`, `.artifacts`) and update .gitignore if new paths are introduced (apps/**/.next, tools/.venv if created).
- Optional: add scaffolding commands (just new-package name, just new-app name) to standardize future additions.

## Out of scope (for this milestone)
- Feature work inside services (no schema or API changes).
- Language/runtime upgrades (Node, Python) beyond what relocation requires.
- Introducing feature flags or transition shims; repo is pre-GA.

## Definition of Done
- Repository matches target layout; all path-sensitive tooling, just recipes, CI workflows, and docs are updated.
- All lint/typecheck/test suites pass from the new locations.
- SNAPSHOTs and README/architecture docs reflect the new structure; newcomers can clone and follow the documented steps without hitting path errors.
