<!-- SECTION: Metadata -->
# Milestone: Stripe TUI One-Stop Integration

_Last updated: 2025-12-24_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Console  
**ID / Links:** [Console charter], [Stripe CLI workflows], [Textual hub]

---

<!-- SECTION: Objective -->
## Objective

Enable Stripe provisioning and webhook setup directly inside the Textual hub so developers can complete billing setup end-to-end without leaving the console, while preserving clean architecture boundaries and reusing existing Stripe workflows.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Textual Stripe pane can run Stripe setup and webhook-secret workflows without subprocesses.
- Interactive prompts and logs render inside the TUI, with clear success/error states.
- Shared prompt runner/adapter reused (no duplicated prompt handling logic).
- Unit tests cover new workflow runner/logging utilities.
- `just lint` and `just typecheck` pass for `packages/starter_console`.
- Tracker updated with changelog entries.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add a reusable Textual workflow runner + prompt controller for interactive workflows.
- Wire Stripe pane buttons to execute Stripe setup and webhook-secret flows directly.
- Show live prompt + output stream in the Stripe pane.
- Update wizard prompt handling to use shared prompt controller (DRY).
- Add console unit tests for new runner/logging utilities.

### Out of Scope
- Redesign of the setup wizard UI beyond prompt controller reuse.
- Changes to Stripe business logic or backend billing flows.
- New product catalog or pricing tiers.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Shared prompt controller + workflow session adapter defined. |
| Implementation | ✅ | Stripe pane runs workflows and surfaces prompts/logs. |
| Tests & QA | ⚠️ | Unit tests added; full suite run interrupted (needs rerun). |
| Docs & runbooks | ✅ | Tracker updated with scope and changelog. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce a Textual workflow session adapter that runs existing console workflows in-process and exposes prompt/log channels.
- Share prompt rendering logic across Wizard and Stripe panes via a reusable prompt controller.
- Stripe pane delegates to existing `run_stripe_setup` and `run_webhook_secret` workflows (no subprocess coupling).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – UI workflow runner

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | UI | Implement reusable workflow session + log/notify adapter | Platform Foundations | ✅ |
| A2 | UI | Implement shared prompt controller and refactor wizard to use it | Platform Foundations | ✅ |

### Workstream B – Stripe pane integration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | UI | Add Stripe pane actions to run setup/webhook in-process | Platform Foundations | ✅ |
| B2 | UI | Display prompt panel + live output + status in Stripe pane | Platform Foundations | ✅ |

### Workstream C – Tests & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Tests | Add unit tests for workflow session + logs | Platform Foundations | ✅ |
| C2 | QA | Run `just lint` + `just typecheck` after each phase | Platform Foundations | ⚠️ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P1 – UI foundations | Workflow session + prompt controller in place | Shared utilities compiled, wizard updated | ✅ | 2025-12-24 |
| P2 – Stripe pane | Stripe pane runs workflows + prompt/log UI | Stripe setup + webhook actions functional | ✅ | 2025-12-24 |
| P3 – QA | Tests + lint/typecheck green | Tests added + checks pass | ⚠️ | 2025-12-24 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Stripe CLI installed for webhook secret capture (interactive).
- Existing Stripe workflows in `starter_console/workflows/stripe/*`.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Prompt handling duplicated across panes | Med | Shared prompt controller utility. |
| UI thread blocking during long workflows | Med | Run workflows in background thread. |
| Stripe CLI auth failures | Low | Surface in TUI logs + status. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && just lint`
- `cd packages/starter_console && just typecheck`
- `cd packages/starter_console && just test` (new unit tests)
- Manual: run `starter-console home`, open Stripe pane, run setup + webhook.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations or config changes required.
- Available through Textual hub after build.
- If Stripe CLI is missing, the flow should surface guidance in the UI.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-24 — Implemented shared prompt controller + workflow session adapter; Stripe pane runs setup/webhook workflows in TUI.
- 2025-12-24 — Added unit tests for workflow session/logging; lint/typecheck green; full test suite rerun pending.
