# Starter Console Setup Hub Milestone

_Last updated: November 21, 2025_

## Objective
Add a dedicated Setup Hub reachable from the Starter Console that inventories operator setup flows, shows progress/state, and lets users launch or resume them. Entry points: `starter-console setup menu` (or `starter-console setup menu`) and the Home TUI shortcut `S` that opens the hub in a fresh run.

## Scope & Deliverables
1) **Setup Hub command** — `setup menu` / alias `setup dashboard` with TUI (Rich) plus `--no-tui` table output for CI.
2) **Setup inventory model** — statuses for wizard, secrets provider, Stripe billing, DB release, usage reports, dev user, and GeoIP dataset where applicable; artifact- and env-based detection with stale/unknown handling.
3) **Navigation hook** — Home dashboard footer shortcut `S` that launches the hub without embedding it into the Home layout.
4) **Actions** — Each setup item exposes primary actions to start/resume (wizard, secrets onboard, stripe setup, release db, usage export/sync, users ensure-dev) and secondary actions where switching providers/profiles makes sense.
5) **Docs** — README/CLI help updated with the new command, shortcut mention, and `--no-tui` usage; tracker maintained.

## Non-Goals
- Replacing the existing Home dashboard layout or doctor flow.
- Introducing feature flags/backcompat shims; this is the first release of the hub.
- Adding new backend probes or changing probe semantics outside the hub status detection.

## Success Criteria
- `starter-console setup menu` renders TUI cards with status badges and lets users trigger actions; `--no-tui` prints a concise table.
- Home TUI shows shortcut `S` and opens the hub; no regressions to Home/Doctor behavior.
- Status detection uses artifacts/env without hitting backend APIs; stale artifacts show as “stale/unknown” rather than “done”.
- Actions reuse existing commands and respect current env loading rules; no cross-imports into `api-service` or `web-app`.
- Unit tests cover status detection, command registration, and shortcut wiring.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Command naming & entry points | ✅ Agreed | Use `setup menu` (+ alias `setup dashboard`); Home shortcut `S`. |
| Scope definition | ✅ Agreed | Inventory items and actions listed above. |
| Status heuristics | ✅ Completed | Artifact/env detection with 7-day staleness window. |
| TUI layout | ✅ Completed | Table/TUI rendering implemented for setup hub. |
| CLI wiring | ✅ Completed | Command + alias registered; Home shortcut wired. |
| Tests & docs | ✅ Completed | Unit tests added; README and tracker updated. |

## Decisions (locked 2025-11-21)
- Artifact staleness: mark artifacts older than 7 days as “stale” instead of “done”.
- Headless output: support `--json` alongside `--no-tui` table output.
- GeoIP card: include as optional; show “not configured” if provider/mmdb missing.
- Env overwrites: interactive runs warn before actions that rewrite `.env.local` / `web-app/.env.local`; headless (`--non-interactive`) skips prompt.
- Progress semantics: wizard uses sections completed/total; Stripe uses three states (missing, keys-only, keys+products+webhook); others are binary.

## Work Plan
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Define `SetupItem` model + status detection (artifacts, env, stale window). | Platform Foundations | ✅ Completed | Nov 2025 |
| 2 | Implement `setup menu` command with TUI + `--no-tui` table; add alias `setup dashboard`. | Platform Foundations | ✅ Completed | Dec 2025 |
| 3 | Wire Home shortcut `S` to launch the hub (new process), keep Home layout unchanged. | Platform Foundations | ✅ Completed | Dec 2025 |
| 4 | Add per-item actions (wizard resume, secrets onboard with provider choice, stripe setup, release db, usage export/sync, users ensure-dev; optional GeoIP refresh) with confirmation when env files may be overwritten. | Platform Foundations | ✅ Completed | Dec 2025 |
| 5 | Tests: status detection unit tests; command registration/args; Home shortcut behavior; `--no-tui` output snapshot. | Platform Foundations | ✅ Completed | Dec 2025 |
| 6 | Docs: README updates, CLI help text, Home shortcut mention, sample `--no-tui` output. | Platform Foundations | ✅ Completed | Dec 2025 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Artifact staleness misreports status | Medium | Mark stale when mtimes exceed threshold; display “stale/unknown” instead of “done”. |
| Env overwrite surprises when re-running flows | Medium | Prompt/warn before actions that write `.env.local`/`web-app/.env.local`; consider `--dry-run` where applicable. |
| TUI coupling to Home | Low | Launch hub in a separate command, keep Home layout untouched; shortcut merely spawns command. |

## Open Questions
None; defaults locked (see Decisions).

## Validation Plan
- Unit tests for detection, command arg parsing, shortcut wiring.
- Manual smoke: `setup menu`, `setup menu --no-tui`, Home `S` shortcut.
- CI gates unchanged; ensure `hatch run lint` / `hatch run typecheck` stay green after integration.
