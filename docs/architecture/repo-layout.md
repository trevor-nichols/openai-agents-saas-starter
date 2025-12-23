# Repository Layout Contract

Defines the target directory layout for the refactor milestone and the rules for adding new apps, packages, and tools. Treat this as the single source of truth when reorganizing or onboarding contributors.

## Target tree (post-refactor)
```
justfile                # root orchestrator delegating to app/package justfiles
ops/                    # infra as code (compose, observability generator)
docs/                   # product/engineering docs, trackers, ADRs
apps/
  api-service/          # FastAPI service (Agents SDK)
  web-app/              # Next.js 16 frontend
packages/
  starter_cli/          # operator CLI
  starter_contracts/    # shared contracts/lib
  starter_providers/    # shared cloud SDK clients
tools/                  # shared scripts (typecheck, smoke, moduleviz, vault helpers)
var/                    # runtime artifacts (keys/, logs/, reports/) — gitignored
.env.compose(.example)  # docker-compose defaults
apps/api-service/.env.local(.example)    # backend runtime secrets
pnpm-workspace.yaml     # JS/TS workspaces (apps/*, packages/*)
tsconfig.scripts.json   # TS settings for tools
.github/                # CI workflows, issue templates
```

## Ownership and boundaries
- **apps/** — Deployable services. No app may import from another app directly; share via packages/.
- **packages/** — Shared libraries and CLIs. Packages must not import from apps/. Favor explicit versioned interfaces over sys.path hacks.
- **tools/** — Cross-repo scripts (smoke tests, env inventory, module graphs). Must remain import-side-effect free and avoid depending on app internals at import time.
- **ops/** — Infra definitions and generators. No business logic lives here; only wiring/config.
- **docs/** — ADRs, runbooks, trackers. Keep repo layout and onboarding docs here.
- **var/** — Runtime data only. Never commit contents; provide README for subfolders (keys, logs, reports).

## Dependency rules
- Allowed graph: tools → packages; apps → packages; packages ↔ packages (careful of cycles); docs may reference anything.
- Disallowed: apps → apps; packages → apps; tools importing app code at import time (runtime imports within main entrypoints are acceptable if guarded).
- Sys.path injections should be replaced with stable importable packages; use package installs or explicit PYTHONPATH variables in just recipes where unavoidable.

## Adding a new unit
1) Choose location: deployable → `apps/<name>`; shared lib → `packages/<name>`; script suite → `tools/<name>`.
2) Add project-level config: justfile (optional), lint/typecheck configs, README, and update `pnpm-workspace.yaml` if JS/TS.
3) Register in root orchestrators: root `justfile` delegates, `tools/typecheck.py` (Python), CI workflows, and SNAPSHOT regenerations.
4) Document ownership and contact in `docs/architecture/services-ownership.md` or a new entry.

## Runtime state policy (var/)
- Keep runtime artifacts under `var/` with subfolders: `keys/` (Ed25519), `logs/` (service logs), `log/` (legacy), `reports/` (CLI outputs).
- `var/` remains gitignored; if a subfolder needs to be tracked, add a README and an allowlist pattern instead of removing the ignore.
- Local dev containers (compose) should mount `var/` consistently; avoid scattering state under apps/.

## Path conventions to respect when moving files
- Root `justfile` delegates to per-project justfiles; compose files live under `ops/compose/`.
- Type/lint runners (`tools/typecheck.py`) list each Python project explicitly; update paths when relocating.
- CLI/sys.path shims currently point to `api-service/`; during relocation, replace with a single helper that resolves `apps/api-service`.
- JS/TS workspace config (`pnpm-workspace.yaml`) must include `apps/*` and `packages/*` after the move.

## Testing and docs
- After adding or relocating directories, regenerate SNAPSHOT.md (root + per-project) to match the new tree.
- Update `README.md` “Repo layout” section to mirror this contract and link back here.
