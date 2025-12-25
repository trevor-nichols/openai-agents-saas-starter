# CLI Home Hub Milestone

_Last updated: November 21, 2025_

## Objective
Deliver a first-class operator “home hub” inside the Starter CLI that surfaces stack status, runs doctor checks, and launches common workflows with an opt-in TUI. The experience should feel like a game-style home menu for non-technical users while remaining testable, modular, and side-effect free for engineers.

## Scope & Deliverables
1) **Home dashboard (TUI + plain output)** — Live view with status cards, quick actions, activity log; keyboard shortcuts; graceful fallback when `--no-tui`.
2) **Doctor checks** — Consolidated probes for env coverage, ports, db/redis readiness, API/FE health, migrations head, optional Stripe/Vault (warn-only for local), emitted as JSON/Markdown for CI artifacts.
3) **Start launcher** — `start dev|backend|frontend` orchestration with health waiters, opt-in browser open, structured summaries, and clean shutdown guidance.
4) **Reports** — Unified operator report at `var/reports/operator-dashboard.{json,md}` combining doctor results and recent actions.
5) **Packaging & ergonomics** — Pipx/uvx-friendly entrypoint; optional TUI extra; console themes accessible via `--console-theme`.

## Non-Goals
- Rewriting the CLI in Rust or changing dependency injection patterns.
- Managing long-running processes that were not started by the CLI (avoid surprise teardown).
- Adding feature flags or transition shims for pre-v0.5.0 stacks.

## Success Criteria
- `python -m starter_cli.app home` renders a navigable hub or a concise summary with `--no-tui`.
- `python -m starter_cli.app doctor --json` exits non-zero on critical failures and emits machine-readable results.
- `python -m starter_cli.app start dev --open-browser` reliably brings up compose + backend + frontend and reports health within a bounded timeout.
- No cross-imports into `api-service` or `web-app`; tests remain hermetic under SQLite/fakeredis overrides.
- Tracker kept current with milestone status per task below.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Architecture doc & tracker | ✅ Drafted | This milestone file defines scope/non-goals and phases. |
| Core models/layout stubs | ⏳ Not started | Need status models, probe interfaces, and UI skeleton. |
| Doctor command | ⏳ Not started | Probes and report renderer pending. |
| Home hub TUI | ⏳ Not started | Layout/components to be built after probes land. |
| Start launcher | ⏳ Not started | Process supervisor + health waiters to implement. |
| Reports/CI wiring | ⏳ Not started | JSON/Markdown emitters and CI recipe TBD. |
| Packaging polish | ⏳ Not started | pipx/uvx instructions + optional Textual extra to add. |

## Work Plan
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Define status models (`ProbeResult`, `ServiceStatus`, `ActionShortcut`, `LaunchPlan`) in `starter_cli/core/status_models.py`. | Platform Foundations | ✅ Completed | Dec 2025 |
| 2 | Add probe library under `starter_cli/workflows/home/probes/` (db, redis, api, frontend, ports, env coverage, migrations, stripe, vault). | Platform Foundations | ✅ Completed | Dec 2025 |
| 3 | Implement `doctor` command composing probes; supports `--json/--markdown/--strict`; warn-only for Stripe/Vault in demo profile. | Platform Foundations | ✅ Completed | Dec 2025 |
| 4 | Build `home` hub workflow + TUI (Rich/Textual) with shortcuts and fallback summary output. | Platform Foundations | ✅ Completed | Dec 2025 |
| 5 | Add `start dev|backend|frontend` orchestrator with process supervision, health polling, and opt-in browser open. | Platform Foundations | ✅ Completed | Dec 2025 |
| 6 | Emit consolidated operator report (`var/reports/operator-dashboard.*`) and document CI usage (`doctor --json --strict`). | Platform Foundations | ✅ Completed | Dec 2025 |
| 7 | Update README/CLI docs; add screenshots/gifs; ensure pipx/uvx guidance and optional TUI extra. | Platform Foundations | ⏳ In progress | Dec 2025 |

## Validation Log
- 2025-11-21: Unit tests `python -m pytest starter_cli/tests/unit/home` ✅
- 2025-11-21: `hatch run typecheck` (pyright + mypy) ✅
- 2025-11-21: Doctor JSON serialization aligned to `doctor_v1` schema (created_at removed from payload) ✅

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| TUI dependency bloat or terminal incompatibility | Medium | Keep TUI optional (`--no-tui`); gate Textual install behind extra; maintain plain-output path. |
| Long-running process supervision surprises users | Medium | Default to attach-and-report; only manage processes started by the CLI; surface PIDs and exit instructions. |
| Probe flakiness in CI (network/API) | Medium | Use timeouts, retries, and mark Stripe/Vault optional for local; provide `--strict` to elevate warnings to errors. |
| Scope creep into backend/web responsibilities | Low | Enforce import boundaries and keep probes subprocess/HTTP based; track in tests. |

## Open Questions
- Should we adopt Textual for richer navigation, or stay with Rich Live for minimal deps? (Default leaning: Textual optional extra.)
- What default health timeout should `start dev` enforce before giving up? (Propose 120s with per-service thresholds.)
- Do we want a JSON schema for doctor output to stabilize integrations? (Likely yes; version it in `starter_contracts`.)

## Changelog
- **2025-11-21** — Milestone created; scope, success criteria, plan, and risks captured.

## Phase Plan & Status
| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| 0 – Decisions & Contracts | Lock UI stack choice; record defaults (timeouts, browser opt-in, Stripe/Vault warn policy); add doctor report JSON schema stub. | Tracker updated with choices; schema added under `starter_contracts/`; open questions resolved for this phase. | ✅ Completed (2025-11-21) |
| 1 – Core Plumbing | Probe interfaces/helpers, timers, shared models finalized. | Probes callable standalone; helper tests passing. | ✅ Completed (2025-11-21) |
| 2 – Doctor Command | Implement probes and doctor assembler with JSON/Markdown emitters and strict mode. | `python -m starter_cli.app doctor` useful; exits non-zero on errors; writes reports. | ✅ Completed (2025-11-21) |
| 3 – Home Hub UI | Live hub + summary fallback; shortcuts wired to probes/actions. | `home` shows statuses; works with/without TUI. | ✅ Completed (2025-11-21) |
| 4 – Start Launcher | Orchestrate dev/backend/frontend starts with health waiters and opt-in browser open. | `start dev` reliably brings stack up or fails fast with guidance. | ✅ Completed (2025-11-21) |
| 5 – Polish & Packaging | Themes, docs, CI recipe, pipx/uvx guidance, optional Textual extra. | Docs and tracker updated; packaging guidance published. | ⏳ Pending |

## Follow-up Execution Plan (clean architecture, no chromatic coupling)
Phased, review-after-each-step cadence. Owners: Platform Foundations unless noted.

| # | Phase | Scope (what we will do) | Exit Criteria | Status | Target |
| - | ----- | ----------------------- | ------------- | ------ | ------ |
| 0 | Baseline alignment | Re-read CLI/contracts/scripts snapshots; reaffirm dependency directions; lock `doctor_v1` contract notes in `status_models.py`; add import-boundary test to prevent `workflows/home/*` from pulling `api-service`/`web-app`. | Tracker updated; boundary test passing; contract comment present. | ✅ Completed (2025-11-21) | Nov 2025 |
| 1 | Probe maturity | Upgrade probes: DB/Redis ping (timeout-bound), migrations head vs DB current, Stripe/Vault auth ping (warn-only local), stricter profile handling; add remediation + metadata; expand unit coverage for failure cases. | All probes return deterministic metadata; unit tests cover success/failure/timeouts; local warns respected. | ✅ Completed (2025-11-21) | Nov 2025 |
| 2 | Doctor robustness | Validate JSON against `doctor_v1` via jsonschema test; exit-code matrix (`--strict`); artifact path override test; add `var/reports/README.md`. | Doctor run fails on schema violations; strict/non-strict behaviors tested; artifacts documented. | ✅ Completed (2025-11-21) | Nov 2025 |
| 3 | Start orchestrator hardening | Add minimal supervisor (PID tracking, prefixed logs, clean shutdown on SIGINT); per-step timeouts; log tail on failure; reuse probes for health; remediation messages. | Start exits cleanly, reports failing step, tails logs on failure; unit tests for flapping health and missing commands. | ✅ Completed (2025-11-21) | Dec 2025 |
| 4 | Home hub TUI | Live refresh loop; optional `[tui]` extra (Textual) while keeping Rich fallback; keyboard shortcuts (rerun probes, open reports, launch start, toggle strict, open browser); summary path stays pure stdout. | `home` interactive mode navigable; `--no-tui` unchanged; view uses only controller callbacks (no subprocess coupling). | ✅ Completed (2025-11-21) | Dec 2025 |
| 5 | Docs & ergonomics | README updates (pipx/uvx + `[tui]` extra, command examples); add small screenshot/GIF; `just doctor` / `just start-dev` helpers; report retention note. | Docs merged; just commands runnable; screenshot linked; CI recipe documented. | ✅ Completed (2025-11-21) | Dec 2025 |
| 6 | Quality gates | Record runs: `hatch run lint`, `hatch run typecheck`, `pytest starter_cli/tests/unit/home`; optional smoke script for doctor without network; update tracker log with dates. | All gates green; tracker log updated; smoke script side-effect free. | ✅ Completed (2025-11-21) | Dec 2025 |

## Phase 0 Decisions
- **UI stack**: Rich remains baseline; Textual added as optional extra (`starter_cli[tui]`) for the hub. Fallback to plain console with `--no-tui`.
- **Doctor schema**: Versioned at `starter_contracts/doctor_v1.json` (draft 2020-12), enumerating probes and services with states `ok|warn|error|skipped`.
- **Health timeouts**: Default overall start timeout 120s; per-service health wait 30s unless overridden by flag. Timeouts will be configurable per command.
- **Strictness policy**: Stripe/Vault probes are warn-only on `demo` profile; elevated to errors under `--strict` or non-demo profiles.
- **Browser open**: Opt-in via `--open-browser`; default is off.
