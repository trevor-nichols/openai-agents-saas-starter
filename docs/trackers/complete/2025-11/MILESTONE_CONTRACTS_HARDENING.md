# Milestone: Contracts Hardening & Platform Guardrails

## Goal
Ship an "optimal" architecture pass: shrink shared surface to a versioned contracts package, harden CI guardrails, and formalize key/secret handling so backend and CLI stay in lockstep without drift.

## Scope
- Backend + CLI only; frontend changes are limited to SDK regen enforcement.
- No environment/channel matrixing; single-track delivery.

## Non-goals
- Standing up new environments.
- Major feature work beyond contracts, validation, CI, and key/secret flows.

## Ownership
- Driver: Codex (assistant) → will mark sign-off for each phase.
- Reviewer: Core maintainers (tbd).

## Phases & Checkpoints

### Phase 1 — Contracts Package
- [x] Publish `starter-contracts` (extract current `starter_contracts`), keep import-safe and side-effect free.
- [x] Add import-boundary tests (only backend + CLI may consume; contracts depend on nothing app-specific).
- [x] Freeze settings/provider schemas (JSON Schema/OpenAPI snippets) and fail CI on drift.
- [x] Document package API surface in `CONTRACTS.md` (or AGENTS.md section).
 - Sign-off: 11/20/2025 by Codex

### Phase 2 — CI Guardrails
- [x] CI job: `just lint`, `hatch run typecheck`, `pnpm lint`, `pnpm type-check`.
- [x] CLI dry-run job: `starter-cli setup --non-interactive --dry-run` (hermetic: SQLite/fakeredis, no network).
- [x] SDK drift check: regenerate HeyAPI client and fail on diff.
- [x] Platform smoke: backend health + JWKS endpoint + one agents-SDK call with fake providers.
 - Sign-off: 11/20/2025 by Codex

### Phase 3 — Release Discipline (Single Track)
- [x] Semantic version bump ties `starter-contracts` + OpenAPI spec; update changelog slice.
- [x] SBOM + dependency audit (pip + pnpm) in CI.
- [ ] Tag + artifact upload for contracts wheel.
- Sign-off: ___/___/2025 by ______

### Phase 4 — Security & Keys
- [ ] CLI key-rotation command: rotate Ed25519, publish JWKS, emit audit artifact.
- [ ] Least-privilege policies doc for Vault/AWS/Azure; CLI check validates required principals/paths.
- [ ] Optional: schedule-aware “next” key handling with expiry metadata.
- Sign-off: ___/___/2025 by ______

### Phase 5 — DX Polish
- [ ] One-command bootstrap target (`just setup-all`): envs, SDK regen, migrations, health smoke.
- [ ] Add `CONTRACTS.md` import graph diagram + quickstart for operators.
- [ ] (Optional) Storybook/MDX gallery for shared UI primitives (if time allows).
- Sign-off: ___/___/2025 by ______

## Risks & Mitigations
- Drift between backend/CLI schemas → addressed via Phase 1 schema freeze + CI drift checks.
- Long CI times → keep smoke hermetic, parallelize lint/typecheck, cache pnpm/pip.
- Secret backend variability → document policies and add validation to reduce surprises.

## Tracking
- Updates and sign-offs will be recorded directly in this file as phases complete.
