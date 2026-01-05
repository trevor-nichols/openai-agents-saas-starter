<!-- SECTION: Metadata -->
# Milestone: CLI Wizard Editor (Curses)

_Last updated: 2026-01-05_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Console  
**ID / Links:** [TBD], [packages/starter_console], [docs/trackers/templates/MILESTONE_TEMPLATE.md]

---

<!-- SECTION: Objective -->
## Objective

Replace the current interactive CLI wizard (`starter-console setup wizard --cli`) with a
pure-terminal, curses-based configuration editor that lets operators navigate sections,
review current values, edit only what they need, and then save or save+run automation.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `starter-console setup wizard --cli` launches the curses editor (no Textual UI).
- Editor shows left section list + right field list with current values and choices.
- Users can edit fields, save env files + reports, or save + run automation.
- Automation action is disabled unless required fields are populated.
- `packages/starter_console/README.md` documents the new CLI editor flow.
- Console lint/typecheck/tests remain green (`hatch run lint`, `hatch run typecheck`).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- New curses-based editor UX for the wizard CLI.
- Field model generated from wizard prompts and current env values.
- Save-only path writes env files + wizard reports (summary, diff, snapshot).
- Save+automation path runs infra/migrations/dev-user flows when ready.

### Out of Scope
- Textual (GUI) changes.
- New feature flags for skipping prompts.
- New backend behavior or schema changes beyond what the editor needs.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⏳ | Curses editor design drafted, implementation pending. |
| Implementation | ⏳ | CLI editor not yet implemented. |
| Tests & QA | ⚠️ | Will need manual smoke + console lint/typecheck. |
| Docs & runbooks | ⚠️ | README updates required after implementation. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- New curses UI replaces the prompt-by-prompt CLI for `setup wizard --cli`.
- Editor is non-linear: left section navigation + right field editor.
- Field metadata derived from wizard prompt calls; values sourced from env files.
- Save-only path writes env + audit artifacts without automation.
- Save+automation path runs infra/migrations/dev-user when required inputs exist.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Editor UX + Model

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Console | Build curses editor layout + navigation | ⏳ |
| A2 | Console | Build field model from wizard prompt definitions | ⏳ |
| A3 | Console | Edit controls for string/bool/choice/secret | ⏳ |

### Workstream B – Save + Automation Paths

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Save-only: env files + reports/snapshots | ⏳ |
| B2 | Console | Save+automation: infra/migrate/dev-user gating | ⏳ |
| B3 | Console | Update CLI wiring + docs | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (self-contained within the Starter Console).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Prompt metadata drift vs wizard logic | Med | Generate field model from prompt calls instead of duplicating specs. |
| Automation runs with missing required values | Med | Gate Save+Automation on required-field checks. |
| Curses UX unclear | Med | Add persistent help/footer and simple key bindings. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Manual smoke:
  - `starter-console setup wizard --cli` (edit + save only)
  - Save+automation path in demo profile with local Docker.
- Run console checks:
  - `cd packages/starter_console && hatch run lint`
  - `cd packages/starter_console && hatch run typecheck`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Replaces the current `--cli` flow (no legacy path retained).
- No migrations required; config persisted to existing env files.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-05 — Milestone created; implementation starting.
