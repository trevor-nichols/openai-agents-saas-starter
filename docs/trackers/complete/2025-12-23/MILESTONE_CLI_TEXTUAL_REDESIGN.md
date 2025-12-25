<!-- SECTION: Metadata -->
# Milestone: Textual-First CLI Hub

_Last updated: 2025-12-23_  
**Status:** Complete (follow-on hardening tracked in `docs/trackers/CLI_MILESTONE.md`)  
**Owner:** @platform-foundations  
**Domain:** CLI  
**ID / Links:** [Docs: starter_cli/README.md], [Tracker: CLI_MILESTONE.md]

---

<!-- SECTION: Objective -->
## Objective

Deliver a Textual-first, interactive CLI hub that feels native and professional, while preserving non-interactive automation commands. The outcome is a clean, maintainable UI architecture where workflows are UI-agnostic and the CLI experience reads as “Textual from day one.”

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Textual hub is the default entrypoint (`starter-cli` with no args).
- Screens implemented: Home, Setup Hub, Wizard, Logs, Infra, Providers, Stripe, Usage.
- All interactive prompts and dashboards use Textual widgets (no Rich console/prompt UI).
- Headless automation commands remain supported with plain stdout/JSON output.
- UI concerns are isolated behind ports/adapters; workflows have no direct UI dependencies.
- Tests updated/added for new UI ports + Textual screens; existing tests adjusted.
- `hatch run lint` and `hatch run typecheck` pass for `packages/starter_cli`.
- Tracker updated with phase completion + changelog entries.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Introduce UI ports (prompt/notify/progress) and presentation adapters.
- Replace Rich-based UI components and prompt flows with Textual equivalents.
- Build Textual hub shell + navigation and the requested screens.
- Remove Rich console usage from interactive flows.
- Update/extend tests to enforce UI boundaries and screen behavior.

### Out of Scope
- Changes to backend APIs or data models.
- New features unrelated to CLI UX redesign.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Textual-first UI boundaries with plain console output for automation. |
| Implementation | ✅ | Hub + screens ship with Textual widgets only. |
| Tests & QA | ✅ | Lint/typecheck green; UI coverage updated. |
| Docs & runbooks | ✅ | Tracker and CLI docs updated for Textual-first UX. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce UI ports (`PromptPort`, `NotifyPort`, `ProgressPort`) to decouple workflows from UI.
- Implement presentation adapters: `TextualPresenter` for interactive UX and `HeadlessPresenter` for automation output.
- Textual hub becomes the default experience and hosts all screens (Home, Setup, Wizard, Logs, Infra, Providers, Stripe, Usage).
- Remove Rich Live dashboards and Rich prompt UI; Textual widgets only for interactive flows.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – UI Architecture

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Ports | Define UI ports and shared presentation contracts. | @platform-foundations | ✅ |
| A2 | Adapters | Implement Textual + headless presenters. | @platform-foundations | ✅ |
| A3 | Migration | Refactor workflows to use ports (no Rich UI). | @platform-foundations | ✅ |

### Workstream B – Textual Hub + Screens

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Shell | Textual hub shell + navigation + command palette. | @platform-foundations | ✅ |
| B2 | Screens | Home + Setup Hub screens (Textual widgets only). | @platform-foundations | ✅ |
| B3 | Screens | Wizard screen (schema-driven prompts). | @platform-foundations | ✅ |
| B4 | Screens | Logs/Infra/Providers/Stripe/Usage screens. | @platform-foundations | ✅ |

### Workstream C – Cleanup + QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Cleanup | Remove Rich UI components and console prompt helpers. | @platform-foundations | ✅ |
| C2 | Tests | Update/add tests for ports + Textual screens. | @platform-foundations | ✅ |
| C3 | QA | Lint + typecheck green after each phase. | @platform-foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Tracker + phased plan | Tracker created + scope agreed | ✅ | 2025-12-23 |
| P1 – UI Ports | Ports + headless presenter + workflow refactors | A1–A3 complete | ✅ | 2025-12-23 |
| P2 – Hub Shell | Textual shell + navigation | B1 complete | ✅ | 2025-12-23 |
| P3 – Core Screens | Home + Setup Hub (Textual) | B2 complete | ✅ | 2025-12-23 |
| P4 – Wizard | Schema-driven Textual wizard | B3 complete | ✅ | 2025-12-23 |
| P5 – Ops Screens | Logs/Infra/Providers/Stripe/Usage | B4 complete | ✅ | 2025-12-23 |
| P6 – Cleanup + QA | Remove Rich UI, tests, lint/typecheck | C1–C3 complete | ✅ | 2025-12-23 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Textual version in `packages/starter_cli/pyproject.toml` (already present).
- No backend changes required.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Large refactor across workflows | High | Phase-based migration, port boundaries, test coverage. |
| Textual UX regressions | Med | Pilot-based tests, screen-level snapshots. |
| Breaking automation flows | Med | Keep headless presenter, ensure CLI subcommands remain. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_cli && hatch run lint`
- `cd packages/starter_cli && hatch run typecheck`
- Targeted pytest modules for updated workflows/screens.
- Manual smoke: `starter-cli` (hub), `starter-cli setup wizard --non-interactive`, `starter-cli logs tail`.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migration or data backfill required.
- Textual hub becomes default with no transitional shims.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-23 — Milestone tracker created; phases + scope defined; lint/typecheck verified.
- 2025-12-23 — P1 complete: UI ports + headless console; workflows refactored; lint/typecheck green.
- 2025-12-23 — P2 complete: Textual hub shell + navigation + command palette; default entry launches hub; lint/typecheck green.
- 2025-12-23 — P3 complete: Home + Setup Hub panes with Textual widgets and view-model helpers; lint/typecheck green.
- 2025-12-23 — P4 complete: Textual wizard pane with schema-aware state + prompt channel; prior Rich wizard UI removed; lint/typecheck green.
- 2025-12-23 — P5 complete: Ops screens (Logs/Infra/Providers/Stripe/Usage) with Textual panes, ops view models, and tests; lint/typecheck green.
- 2025-12-23 — P6 complete: removed Rich console/table dependencies, simplified setup hub table output, docs updated; lint/typecheck green.

---

<!-- SECTION: Follow-on -->
## Follow-on Hardening (Tracked Separately)

See `docs/trackers/CLI_MILESTONE.md` for the active “Textual Hub Hardening (Ports + Hub Service)” milestone. This covers:
- UI ports + presenter adapters (Textual + headless).
- HubService for aggregated pane data.
- Removal of UI → command module dependencies.
- CLI subcommands as automation entrypoints for the same workflows.
- Removal of `sys.path` injection and associated doc/test updates.
