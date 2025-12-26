# CLI Detached Start/Stop & Stack Status Milestone

_Last updated: November 21, 2025_

## Objective
Deliver a background-capable `start dev` experience with clean stop, PID tracking, and visible stack status in the TUI header. Operators should be able to launch the stack, return to the menu, see live status, and stop only the processes the CLI started.

## Scope & Deliverables
- Detached start mode that records PIDs/logs and returns control to the TUI.
- Stop command that terminates managed PIDs and tears down infra it started.
- Stack state store under `var/run/stack.json` with atomic writes and health/status helpers.
- TUI badges + shortcuts for stack running/stopped, plus log quick-open.
- Stack probe that reports running/degraded/stopped and surfaces in services table.
- Log files per process with lightweight rotation; remediation for port collisions.
- Docs + tracker updates; unit coverage for state/probe/commands/TUI dispatch.

## Non-Goals
- Managing arbitrary user-run processes (only what the CLI launches).
- Adding feature flags or backward compatibility for pre-v0.5.0 flows.
- Replacing docker-compose or existing `just dev-up` automation.

## Success Criteria
- `starter-console start dev --detached` starts infra/backend/frontend, writes PID/log state, and exits 0 after health passes.
- `starter-console stop` stops only tracked PIDs, runs `docker compose down` when infra was ours, and clears state.
- Home TUI shows a stack badge (running/degraded/stopped), refreshes after start/stop, and exposes Start/Stop/Logs shortcuts.
- Stack probe reports OK/WARN/ERROR aligned with live PIDs and health checks; doctor output includes it.
- Unit tests cover state persistence, probe outputs, start/stop commands, and TUI action wiring.

## Work Plan
| # | Task | Status | Owner | Target |
| - | ---- | ------ | ----- | ------ |
| 1 | Add stack state manager (`var/run/stack.json`) with load/save/is_alive/stop helpers (atomic writes). | ✅ Completed | Platform Foundations | Nov 2025 |
| 2 | Extend `start` command: `--detached/--foreground/--force/--log-dir/--pidfile`; detached mode writes state + log files; reuse health wait. | ✅ Completed | Platform Foundations | Nov 2025 |
| 3 | Add `stop` command that reads state, SIGTERM/SIGKILLs managed PIDs, optional compose down when infra started, then clears state. | ✅ Completed | Platform Foundations | Nov 2025 |
| 4 | Introduce stack probe + integrate into services table and doctor summary; add detail metadata (pids, logs, missing processes). | ✅ Completed | Platform Foundations | Nov 2025 |
| 5 | TUI UX: header badge, Start (detached) + Stop + Open Logs shortcuts; actions refresh status after execution; handle empty/off states gracefully. | ✅ Completed | Platform Foundations | Nov 2025 |
| 6 | Logging/rotation: per-process logs under `var/log`, 3x5MB rotation; include paths in state and TUI log shortcut. | ✅ Completed | Platform Foundations | Nov 2025 |
| 7 | Port collision guard: reuse ports probe before launch; block unless `--force` clears only tracked PIDs; no killing foreign processes. | ✅ Completed | Platform Foundations | Nov 2025 |
| 8 | Tests: unit coverage for stack_state, start(detached), stop, stack probe, TUI actions; update snapshots if required. | ✅ Completed | Platform Foundations | Nov 2025 |
| 9 | Docs: README/CLI help updates; tracker updates per task completion; add short “usage” snippet for detached workflow. | ✅ Completed | Platform Foundations | Nov 2025 |

## Validation Plan
- Run: `hatch run lint`, `hatch run typecheck`, `pytest starter_console/tests/unit` (focus on new modules), `pnpm lint`, `pnpm type-check` (front-end bindings).
- Manual: `starter-console start dev --detached`, verify badge + doctor stack probe; `starter-console stop`, confirm ports freed and state cleared.

Validation log:
- 2025-11-21 — `python -m pytest starter_console/tests/unit/home/test_stack_state.py starter_console/tests/unit/home/test_stop_command.py starter_console/tests/unit/home/test_start_runner.py` ✅
- 2025-11-21 — `starter-console start dev --detached` ❌ backend exited during migrations (alembic script_location not found) and frontend saw PORT=8000 clash; stack not recorded; cleaned up with `docker compose down`.
- 2025-11-21 — Remediation applied: StartRunner now pins backend CWD to repo root, injects per-process env overlays (frontend PORT=3000, backend ALEMBIC_* abs paths, drops inherited PORT), and engine config sets absolute Alembic script_location. Added port guard coverage + env tests. Pending re-validation of start/stop after fixes.

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| PIDs become stale (process exited) leaving “running” badge | Medium | `is_alive` check on load; degrade status; stop clears stale entries. |
| Log growth from background runs | Low | Enforce simple rotation (size/N). |
| Killing user processes not started by CLI | Medium | Only act on tracked PIDs; require `--force` and still limit to tracked items. |
| Textual refresh lag after commands | Low | Trigger `refresh_data()` after start/stop actions; debounce updates. |

## Reporting Cadence
- Update the table above after each task completes or materially changes.
- Note validation commands/results in this file when phases close.
