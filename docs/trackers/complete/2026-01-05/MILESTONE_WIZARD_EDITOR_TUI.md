<!-- SECTION: Metadata -->
# Milestone: Wizard Editor TUI Integration

_Last updated: 2026-01-06_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Console  
**ID / Links:** N/A

---

<!-- SECTION: Objective -->
## Objective

Deliver a production-grade Textual Wizard Editor that lets operators review and edit setup
wizard fields side-by-side, then save (optionally with automation) through the existing
setup editor workflow.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Wizard Editor pane exists in the TUI navigation and loads without registry errors.
- Sections/fields render with filtering, descriptions, and prompt editing.
- Save and Save+Automation invoke `apply_and_save` with correct profile + paths.
- Automation run is blocked when required values are missing.
- UI exposes status + output feedback, and dirty state is reflected.
- Console lint/typecheck pass (when run).
- Tracker updated with a changelog entry.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Wizard Editor Textual pane + layout wiring.
- Data refresh using `workflows.setup.editor.sources.collect_sections`.
- Save/automation integration via `workflows.setup.editor.actions.apply_and_save`.
- TUI styling for editor layout and prompt area.

### Out of Scope
- Redesign of the underlying setup wizard schema or CLI editor.
- New automation phases or workflow behaviors.
- Comprehensive TUI test harnesses (not present in repo).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Reuses existing editor sources/actions; minimal new surface area. |
| Implementation | ✅ | Pane + wiring complete; pending verification. |
| Tests & QA | ⏳ | Manual check + lint/typecheck planned. |
| Docs & runbooks | ✅ | Milestone tracker added. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- New Textual pane (`ui/panes/wizard_editor/pane.py`) orchestrates editor state.
- Editor pulls from `workflows.setup.editor` sources (dry-run) and persists via actions.
- Save runs through `ActionRunner` to keep UI responsive and to surface logs.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – TUI Pane + State

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | UI | Add Wizard Editor pane + layout integration | ✅ |
| A2 | UI | Section/field selection, filtering, prompt editing | ✅ |
| A3 | UI | Styling for editor layout + prompt area | ✅ |

### Workstream B – Workflow Wiring

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Wire profile selection + answers | ✅ |
| B2 | Console | Save + Save+Automation via `apply_and_save` | ✅ |
| B3 | Console | Status/output feedback + dirty state | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None beyond existing `workflows.setup.editor` modules.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Save/automation blocks UI | Med | Run via `ActionRunner` and periodic output refresh. |
| Missing required values | Low | Block Save+Automation and surface status. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- Manual TUI smoke: open Wizard Editor, edit a field, save, and verify status/output.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Available via TUI navigation: Onboarding → Wizard Editor.
- No migrations or env changes required.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-06 — Implemented Wizard Editor TUI pane + wiring; pending validation.
