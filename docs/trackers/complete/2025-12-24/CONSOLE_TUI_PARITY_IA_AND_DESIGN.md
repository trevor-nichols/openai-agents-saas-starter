# Console TUI Parity — Information Architecture & Textual Design Notes

_Last updated: 2025-12-24_

## 1) Information Architecture (IA)

Goal: A clean, professional navigation model that mirrors operator intent and avoids pragmatic coupling to command names.

### Category Tree (Collapsible Nav)

**Overview**
- **Home** — health probes + services summary (current home pane)
- **Setup Hub** — setup progress + quick actions (current setup pane)
- **Doctor** — run readiness checks, export JSON/Markdown (new)

**Onboarding**
- **Wizard** — guided setup (current wizard pane)
- **Secrets Onboarding** — provider selection + setup (current modal, promoted to pane or modal entry)
- **Providers Validation** — validation status + strict toggle (current providers pane)

**Operations**
- **Start/Stop** — start targets, detach, logs, pidfile, stop flow (new)
- **Infra** — compose/vault actions + deps (current infra pane, expanded)
- **Logs** — tail + archive + filters (current logs pane, expanded)

**Security & Auth**
- **Auth Tokens** — issue service-account tokens (new)
- **Key Rotation** — rotate signing keys (new)
- **JWKS** — print JWKS payload (new)

**Billing & Usage**
- **Stripe** — setup + webhook secret + dispatch tools (current stripe pane, expanded)
- **Usage** — export report + sync entitlements (current usage pane, expanded)

**Release & Admin**
- **Release DB** — migrations + Stripe seed + verification (new)
- **Config Inventory** — schema dump + inventory export (new)
- **API Export** — OpenAPI export (new)

**Advanced** (power-user, non-routine)
- **Status Ops** — subscriptions list/revoke + incident resend (new)
- **Util: Run with Env** — merge env files and exec command (new)

Notes:
- “Secrets Onboarding” remains a modal launched from Setup Hub and is now also a first-class pane entry for parity and discoverability.
- “Doctor” is placed under Overview because it is diagnostic and summary-heavy; this keeps the operator mental model clean.
- “Advanced” contains the least-frequent workflows per your guidance.

---

## 2) Textual Implementation Patterns (Technical Design)

### 2.1 Principles
- **Presentation only**: TUI must not re-implement domain logic. It calls workflows/services used by the console.
- **Service boundary enforced**: panes do not import console command modules; commands are thin arg parsers → services.
- **Consistency**: Every action pane uses a uniform “Form → Run → Output/Log → Status” structure.
- **Extensibility**: New panes must be easy to add without touching core app logic.
- **Minimal coupling**: TUI should not require deeper knowledge of workflow internals; it should pass inputs and render outputs.

### 2.2 Layout Overview
- **Left nav**: collapsible category groups with pane items.
- **Global Context panel** (header or right panel):
  - env files list (add/remove)
  - toggle `skip env` / `quiet env`
  - reload env button
  - current profile detection (ENVIRONMENT)
- **Content switcher**: active pane

### 2.3 Core UI Components (proposed/implemented)
- **`BasePane`** (planned): common scaffolding for status text, output panel, and action bar.
- **`ActionForm`** (planned): composable input section for flags/parameters; form input validators.
- **`WorkflowRunner`** (implemented): standard wrapper to run workflows with log streaming + prompt channel integration.
- **`ActionRunner`** (implemented): standardized runner for non-interactive workflows with output/status hooks.
- **`StatusTable`** (existing DataTable usage): standardized table headings + empty state messaging.

### 2.4 Navigation Model
- **`SectionSpec` becomes `NavGroup` + `NavItem`**
  - `NavGroup` (label, description, expanded)
  - `NavItem` (key, label, pane factory)
- Textual `ListView` (current) can be replaced with grouped sections or multiple ListViews per category.
- Command palette should list both groups and items.

### 2.5 Global Context Panel
- Backed by existing console env logic:
  - Use `starter_console.app` environment loading logic (default + overrides).
  - Toggle and reload should rehydrate `CLIContext` and notify panes.
- Proposed behavior:
  - When env settings change, prompt to reload. On reload, update `HubService` snapshots and refresh active pane.
- Avoid mutable global state; use a single source of truth for env configuration.
- **Implemented behavior**:
  - Env loads are applied as a tracked overlay. “Skip env load” clears the overlay and restores the pre-TUI environment, preventing stale `.env` values from leaking across actions.
  - Context panel reflects the console’s initial `skip/quiet` flags and surfaces them in the summary for auditability.

### 2.6 API Export Boundary
- OpenAPI export runs via `apps/api-service/scripts/export_openapi.py` so the console never imports backend modules directly.

### 2.7 Workflow Execution Pattern
- **Long-running workflows** (wizard, stripe, secrets) use prompt channels.
- Shared runners:
  - `InteractiveWorkflowSession` + `WorkflowRunner` for workflows with prompts
  - `ActionRunner` for direct (non-interactive) runs
- Provide consistent log buffer handling (max lines + snapshot), with optional export.

### 2.8 Prompt Handling
- Continue using `PromptController` for interactive workflows.
- Standardize “Prompt UI block” pattern across panes.
- Ensure prompt context includes `key`, `default`, `required`, `choices` display.

### 2.9 Output Handling
- Capture:
  - workflow logs (stream)
  - resulting artifacts (paths)
  - status summary
- Surface output in:
  - “Output” panel for logs
  - “Results” table for structured output
  - “Artifacts” section for file paths

### 2.10 Error Handling & UX
- All failures render a consistent error banner + log output
- If workflow returns structured errors, render in a table for readability
- Avoid silent failures

### 2.11 Testing Strategy
- Extend existing UI tests for:
  - pane mount + action execution
  - env reload
  - navigation groups
- Console parity testing: ensure each console command has a TUI equivalent or documented exclusion

---

## 3) Pane Pattern Templates (Reusable)

### Pattern A — Action + Status (e.g., Doctor, Config, API Export)
- Action form
- Run button
- Status table
- Output log

### Pattern B — Interactive Workflow (e.g., Wizard, Stripe, Secrets)
- Action form
- Prompt block
- Workflow log
- Status/summary

### Pattern C — Read-only Snapshot (e.g., Home, Providers, Usage)
- Summary block
- Data tables
- Refresh action

### Pattern D — Mixed Actions (e.g., Infra, Logs)
- Action buttons grouped by subsystem
- Output panel
- Snapshot status table

---

## 4) Design Decisions Pending

- Secrets Onboarding surface resolved: modal + full pane.
- Whether command palette should include advanced panes by default.
- **Resolved:** Start/Stop delivered as a single pane (no tabs).

---

## 5) Next Step (Phase 3)

Phase 3 parity expansion delivered:
- Status Ops and Run-with-Env panes added.
- Secrets Onboarding pane now mirrors console flags.
- Resolve Secrets Onboarding surface decision.
- Polish shared UI patterns (BasePane/ActionForm) if needed.
