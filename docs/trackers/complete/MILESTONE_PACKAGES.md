# Architecture Package Isolation

Goal: reshape the repo into clear, per-surface packages using a `src/` layout, with the root acting only as an orchestrator. Target is an onboarding-friendly, auditable structure that matches production builds.

Status: Phase 1 completed (backend `src/` layout + pyproject). Phase 2 completed: per-package pyprojects + `src/` layouts for `starter_contracts` and `starter_cli` are in place; lint/typecheck/test are green per package. CI wiring drafted; ready to finalize once root cleanup lands.

## Target structure (high level)
- `/` (orchestration only): root `justfile`, docker-compose files, repo-wide docs, pnpm workspace config for JS, minimal tooling config if needed.
- `api-service/`: `pyproject.toml`, `justfile` (backend tasks), `src/app`, `src/run.py`, `alembic/`, `tests/`, `.env*`.
- `starter_cli/`: `pyproject.toml`, `src/starter_cli`, `tests/`.
- `starter_contracts/`: `pyproject.toml`, `src/starter_contracts`, `tests/`.
- `web-app/`: unchanged; owns its `package.json`, lint/typecheck configs.
- `scripts/` and `ops/`: shared utilities; avoid importing app code directly.

Tooling rules: each Python package self-owns `ruff`, `mypy/pyright`, coverage config; Hatch/uv env scoped per package. Root commands delegate into the package (`cd api-service && hatch run serve`, etc.).

## Milestone plan

### Phase 0 – Baseline inventory
- Record current commands and paths (`justfile`, `scripts/typecheck.py`, docker-compose service names).
- Freeze current CI expectations and env files used by automation.

### Phase 1 – Backend `src/` layout
- Move `api-service/app` → `api-service/src/app`; `run.py` → `api-service/src/run.py`.
- New `api-service/pyproject.toml` (build backend only); update entry points to `run:main`.
- Update `alembic.ini` `prepend_sys_path` to `src`; adjust import paths in `alembic/env.py` if needed.
- Update tooling paths (`ruff`, `mypy`, `pyright`, coverage) to point at `src`.
- Update `scripts/typecheck.py` and root `justfile` commands to call the new paths.
- ✅ Completed.

### Phase 2 – CLI and contracts extraction
- Add `starter_cli/pyproject.toml` and `src/starter_cli`; same for `starter_contracts`.
- Remove CLI/contracts packages from backend build configuration; adjust `PYTHONPATH` expectations in tests.
- Ensure CLI entry points (`starter-cli`, `aa-cli`) resolve from the new package.
- Update CI to run lint/typecheck/test per-package (backend, CLI, contracts, frontend).
- ✅ Completed: packages + `src/` layout in place; lint/typecheck/test green for api-service, starter_cli, starter_contracts; CLI dev extras updated to cover shared fixtures; import-boundary tests adjusted.

### Phase 3 – Root cleanup
- Remove backend-specific files from root (`run.py`, backend build config).
- Slim root `pyproject.toml` to tooling-only or drop if unused.
- Keep root `justfile` as an orchestrator delegating to subproject justfiles (or call `hatch`/`uv` with working directories).
- Verify docker-compose scripts and env runners still function (update paths they mount/copy).

### Phase 4 – CI and developer workflow
- Update CI jobs to run per-package lint/typecheck/test (`api-service`, `starter_cli`, `starter_contracts`, `web-app`).
- Cache Python/Node deps per package; ensure artifact paths match the `src` layout.
- Add a short onboarding doc section describing the new commands.

### Phase 5 – Docs and snapshots
- Refresh `README.md`, `AGENTS.md`, relevant `SNAPSHOT.md` files.
- Document the architecture in `docs/architecture/` and link the milestone tracker.
- Add a concise “repo map” diagram reflecting the final layout.

### Phase 6 – Stabilization
- Run full test matrix: `hatch run lint/typecheck/test` (backend, CLI, contracts), `pnpm lint`, `pnpm type-check`, `pnpm test` (web-app).
- Cut a tagged pre-release (`0.2.0` proposed) once parity is confirmed.

## Acceptance criteria
- Each Python surface builds and runs from its own `pyproject.toml` and `src/` tree.
- Root contains no executable Python entry points or package build config.
- `just` and CI pipelines succeed using the new paths.
- Onboarding doc shows one-liners per surface that work on a clean clone.

Current blockers to acceptance:
- Root cleanup + CI split still pending (Phases 3–4).

## Risks and mitigations
- Path drift in Alembic or env loaders: cover with a smoke test that runs `alembic upgrade head` in CI against SQLite.
- Import leakage via `PYTHONPATH=.` assumptions: enforce `src` layout and add a guard test that fails when imports resolve without `src` on sys.path.
- Tooling gaps after moves: keep a temporary compatibility layer (`scripts/typecheck.py`) updated first; run all linters before proceeding to next phase.
