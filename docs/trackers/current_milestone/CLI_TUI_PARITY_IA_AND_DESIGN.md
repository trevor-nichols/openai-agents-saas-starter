# CLI TUI Parity — Information Architecture & Textual Design Notes

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
- “Secrets Onboarding” can remain a modal launched from Setup Hub, but should also appear as a first-class pane entry for parity and discoverability.
- “Doctor” is placed under Overview because it is diagnostic and summary-heavy; this keeps the operator mental model clean.
- “Advanced” contains the least-frequent workflows per your guidance.

---

## 2) Textual Implementation Patterns (Technical Design)

### 2.1 Principles
- **Presentation only**: TUI must not re-implement domain logic. It calls workflows/services used by CLI.
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

### 2.3 Core UI Components (proposed)
- **`BasePane`** (new): common scaffolding for status text, output panel, and action bar.
- **`ActionForm`** (new): composable input section for flags/parameters; form input validators.
- **`WorkflowRunner`** (new): standard wrapper to run workflows with log streaming and prompt channel integration.
- **`StatusTable`** (existing DataTable usage): standardized table headings + empty state messaging.

### 2.4 Navigation Model
- **`SectionSpec` becomes `NavGroup` + `NavItem`**
  - `NavGroup` (label, description, expanded)
  - `NavItem` (key, label, pane factory)
- Textual `ListView` (current) can be replaced with grouped sections or multiple ListViews per category.
- Command palette should list both groups and items.

### 2.5 Global Context Panel
- Backed by existing CLI env logic:
  - Use `starter_cli.app` environment loading logic (default + overrides).
  - Toggle and reload should rehydrate `CLIContext` and notify panes.
- Proposed behavior:
  - When env settings change, prompt to reload. On reload, update `HubService` snapshots and refresh active pane.
- Avoid mutable global state; use a single source of truth for env configuration.

### 2.6 Workflow Execution Pattern
- **Long-running workflows** (wizard, stripe, secrets) already use prompt channels.
- Generalize into a shared runner:
  - `InteractiveWorkflowSession` for workflows with prompts
  - `NonInteractiveWorkflowSession` for direct run methods
- Provide consistent log buffer handling (max lines + snapshot), with optional export.

### 2.7 Prompt Handling
- Continue using `PromptController` for interactive workflows.
- Standardize “Prompt UI block” pattern across panes.
- Ensure prompt context includes `key`, `default`, `required`, `choices` display.

### 2.8 Output Handling
- Capture:
  - workflow logs (stream)
  - resulting artifacts (paths)
  - status summary
- Surface output in:
  - “Output” panel for logs
  - “Results” table for structured output
  - “Artifacts” section for file paths

### 2.9 Error Handling & UX
- All failures render a consistent error banner + log output
- If workflow returns structured errors, render in a table for readability
- Avoid silent failures

### 2.10 Testing Strategy
- Extend existing UI tests for:
  - pane mount + action execution
  - env reload
  - navigation groups
- CLI parity testing: ensure each CLI command has a TUI equivalent or documented exclusion

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

- Whether Secrets Onboarding is a modal only or also a full pane (recommended: both).
- Whether Start/Stop is one pane with tabs or split panes.
- Whether command palette should include advanced panes by default.

---

## 5) Next Step (Phase 1)

- Implement grouped nav and global context panel.
- Introduce shared workflow runner and action form components.
- Update Wizard/Setup/Logs/Infra/Providers/Stripe panes to use the shared pattern.

