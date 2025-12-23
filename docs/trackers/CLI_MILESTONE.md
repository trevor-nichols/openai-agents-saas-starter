<!-- SECTION: Metadata -->
# CLI Roadmap & Status

_Last updated: 2025-12-23_  
**Owner:** @platform-foundations  
**Domain:** CLI  
**Scope:** Roadmap tracking + active milestone status.

---

## Active Milestone

### Milestone: Textual Hub Hardening (Ports + Hub Service)

**Status:** In Progress  
**Goal:** Make the Textual hub the authoritative UI surface while keeping CLI subcommands as automation-mode entrypoints, with clean UI boundaries and a shared hub data model.

#### Definition of Done
- UI boundaries are enforced via ports (`PromptPort`, `NotifyPort`, `ProgressPort`) and presenter adapters.
- Textual hub uses the same workflows as headless commands (no duplicate logic).
- A `HubService` aggregates pane data and is used by both TUI and headless outputs.
- UI no longer imports CLI command modules; shared logic lives in services/workflows.
- `__init__.py` no longer mutates `sys.path`.
- CLI snapshot + docs updated; tests added/adjusted for ports/presenters/hub.
- `cd packages/starter_cli && hatch run lint && hatch run typecheck` pass.

#### Remediation Plan (Post-Review)
- Replace Setup Hub subprocess actions with routed TUI actions (no nested CLIs).
- Route secrets onboarding through Textual prompt ports (same as wizard flow).
- Remove remaining raw `input()` calls from secrets workflows.
- Update snapshot + add tests for ports/presenters + UI action routing.

#### Workstreams

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Ports | Introduce UI ports + presenter interfaces. | @platform-foundations | ⏳ |
| A2 | Presenters | Implement Textual + headless presenters. | @platform-foundations | ⏳ |
| B1 | Hub Service | Centralize pane data into `HubService`. | @platform-foundations | ⏳ |
| B2 | Dependency Cleanup | Move UI-facing helpers out of command modules. | @platform-foundations | ⏳ |
| B3 | Workflow Integration | TUI + CLI subcommands use shared workflows. | @platform-foundations | ⏳ |
| C1 | Sys Path Cleanup | Remove backend `sys.path` injection. | @platform-foundations | ⏳ |
| C2 | Docs + Tests | Update snapshots/docs + add test coverage. | @platform-foundations | ⏳ |
| D1 | TUI Actions | Replace Setup Hub subprocess actions with routed TUI actions. | @platform-foundations | ✅ |
| D2 | Secrets TUI | Route secrets onboarding through Textual prompt ports. | @platform-foundations | ✅ |
| D3 | Secrets Prompts | Remove raw input() usage in secrets flows. | @platform-foundations | ✅ |
| D4 | Snapshot + Tests | Refresh CLI snapshot + add tests for ports/presenters/UI routing. | @platform-foundations | ✅ |

---

## Completed Milestones

### Textual-First CLI Hub (2025-12-23)
- Default Textual hub entrypoint with core screens.
- Rich-based interactive UI removed from the hub flow.
- Headless commands preserved for automation.
- Tracker: `docs/trackers/current_milestone/MILESTONE_CLI_TEXTUAL_REDESIGN.md`.

---

## Roadmap (Upcoming / Proposed)

1. Stripe module split: break `commands/stripe.py` into smaller workflow/service modules.
2. Extract remaining command-bound helpers used by wizard sections (auth/stripe) into services.
3. Screen-level integration tests using Textual test harness.
4. Additional ops panes (billing events, agents, workflows) as needed.
