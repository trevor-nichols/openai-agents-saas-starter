# Console ↔ TUI Parity Checklist

_Last updated: 2025-12-24_

Scope: map every console command/subcommand to a TUI pane/screen and note missing controls. Source of truth is `packages/starter_console/SNAPSHOT.md` plus current Textual panes.

## TUI Surfaces (current)
- Home pane (`home`)
- Setup Hub pane (`setup`)
- Wizard pane (`wizard`)
- Doctor pane (`doctor`)
- Start/Stop pane (`start-stop`)
- Logs pane (`logs`)
- Infra pane (`infra`)
- Providers pane (`providers`)
- Stripe pane (`stripe`)
- Usage pane (`usage`)
- Release DB pane (`release-db`)
- Config Inventory pane (`config-inventory`)
- API Export pane (`api-export`)
- Auth Tokens pane (`auth-tokens`)
- Key Rotation pane (`key-rotation`)
- JWKS pane (`jwks`)
- Secrets Onboarding pane (`secrets`)
- Status Ops pane (`status-ops`)
- Run With Env pane (`util-run-with-env`)
- Global Context panel (env files + reload controls)
- Secrets Onboarding modal (opened from Setup Hub)

## Global Console Flags (surfaced inside TUI)
- `--env-file <path>` (additional env files)
- `--skip-env` (skip default env loading)
- `--quiet-env` (suppress env load logs)
Note: Context panel updates the environment in-memory and can be reloaded without restarting the TUI.

## Command → TUI Mapping
Legend: **Full** = equivalent controls in TUI, **Partial** = some controls missing, **None** = no TUI surface.

| Console command (path) | TUI surface | Parity | Missing knobs / behavior |
| --- | --- | --- | --- |
| `home` | Home pane | Full | None. (`--no-tui` is console-only by design.) |
| `doctor` | Doctor pane | Full | None. |
| `setup menu` | Setup Hub pane | Full | None. |
| `setup wizard` | Wizard pane | Full | None. |
| `secrets onboard` | Secrets Onboarding pane | Full | None. |
| `infra compose <up|down|logs|ps>` | Infra pane | Full | None. |
| `infra vault <up|down|logs|verify>` | Infra pane | Full | None. |
| `infra deps` | Infra pane | Full | None. |
| `logs tail` | Logs pane | Full | None. |
| `logs archive` | Logs pane | Full | None. |
| `providers validate` | Providers pane | Full | None. |
| `stripe setup` | Stripe pane | Full | None. |
| `stripe webhook-secret` | Stripe pane | Full | Matches `--forward-url`, `--print-only`, `--skip-stripe-cli`. |
| `stripe dispatches list` | Stripe pane | Full | None. |
| `stripe dispatches replay` | Stripe pane | Full | None. |
| `stripe dispatches validate-fixtures` | Stripe pane | Full | None. |
| `usage export-report` | Usage pane | Full | None. |
| `usage sync-entitlements` | Usage pane | Full | None. |
| `auth tokens issue-service-account` | Auth Tokens pane | Full | None. |
| `auth keys rotate` | Key Rotation pane | Full | None. |
| `auth jwks print` | JWKS pane | Full | None. |
| `config dump-schema` | Config Inventory pane | Full | None. |
| `config write-inventory` | Config Inventory pane | Full | None. |
| `api export-openapi` | API Export pane | Full | None. |
| `release db` | Release DB pane | Full | None. |
| `start` | Start/Stop pane | Full | None. |
| `stop` | Start/Stop pane | Full | None. |
| `status subscriptions list` | Status Ops pane | Full | None. |
| `status subscriptions revoke` | Status Ops pane | Full | None. |
| `status incidents resend` | Status Ops pane | Full | None. |
| `users ensure-dev` | None | None | Console-only; out of scope for TUI parity. |
| `users seed` | None | None | Console-only; out of scope for TUI parity. |
| `util run-with-env` | Run With Env pane | Full | None. |

## Notes / Design Considerations
- The Wizard pane now surfaces headless console knobs (answers files, non-interactive mode, report-only, export paths, automation overrides).
- The Setup Hub pane executes command-based actions in-place and captures output.
- Logs/Infra/Providers/Usage panes expose the console export/strict controls where applicable.
- TUI panes call service/workflow modules directly (presentation-only); console commands remain thin arg adapters.
