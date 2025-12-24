# CLI ↔ TUI Parity Checklist

Scope: map every CLI command/subcommand to a TUI pane/screen and note missing controls. Source of truth is `packages/starter_cli/SNAPSHOT.md` plus current Textual panes.

## TUI Surfaces (current)
- Home pane (`home`)
- Setup Hub pane (`setup`)
- Wizard pane (`wizard`)
- Logs pane (`logs`)
- Infra pane (`infra`)
- Providers pane (`providers`)
- Stripe pane (`stripe`)
- Usage pane (`usage`)
- Secrets Onboarding modal (opened from Setup Hub)

## Global CLI Flags (not surfaced inside TUI)
- `--env-file <path>` (additional env files)
- `--skip-env` (skip default env loading)
- `--quiet-env` (suppress env load logs)
Note: these can be supplied when launching the TUI, but are not adjustable once inside it.

## Command → TUI Mapping
Legend: **Full** = equivalent controls in TUI, **Partial** = some controls missing, **None** = no TUI surface.

| CLI command (path) | TUI surface | Parity | Missing knobs / behavior |
| --- | --- | --- | --- |
| `home` | Home pane | Full | None. (`--no-tui` is CLI-only by design.) |
| `doctor` | None | None | All flags: `--profile`, `--json`, `--markdown`, `--strict`. Home pane shows doctor probes but cannot run/export doctor reports. |
| `setup menu` | Setup Hub pane | Partial | No JSON output (`--json`). Action execution is limited: for items with `command`, TUI only prints "Run: ..." instead of executing. |
| `setup wizard` | Wizard pane | Partial | Missing flags: `--strict`, `--non-interactive`, `--no-schema`, `--report-only`, `--output`, `--answers-file`, `--var`, `--export-answers`, `--summary-path`, `--markdown-summary-path`, `--auto-*` overrides. |
| `secrets onboard` | Secrets Onboarding modal | Partial | No `--non-interactive`, `--answers-file`, `--var`, `--skip-automation`. Provider selection is in TUI but not pre-seeded from CLI args. |
| `infra compose <up|down|logs|ps>` | Infra pane | Partial | Only `up/down` buttons. Missing `logs`, `ps`. |
| `infra vault <up|down|logs|verify>` | Infra pane | Partial | Only `up/down` buttons. Missing `logs`, `verify`. |
| `infra deps` | Infra pane | Partial | Table is shown, but no `--format json` export or CLI-style output. |
| `logs tail` | Logs pane | Partial | Fixed targets (API + CLI only), fixed lines=200, no `--service`, `--lines`, `--follow/--no-follow`, `--errors` for all services, or custom `--log-root`. |
| `logs archive` | None | None | All flags: `--days`, `--log-root`, `--dry-run`. |
| `providers validate` | Providers pane | Partial | No `--strict` toggle. TUI always uses settings-driven strictness. |
| `stripe setup` | Stripe pane | Partial | Missing `--non-interactive`, `--secret-key`, `--webhook-secret`. TUI always runs interactive flow. |
| `stripe webhook-secret` | Stripe pane | Full | Matches `--forward-url`, `--print-only`, `--skip-stripe-cli`. |
| `stripe dispatches list` | None | None | All flags: `--status`, `--handler`, `--limit`, `--page`. |
| `stripe dispatches replay` | None | None | All flags: `--dispatch-id`, `--event-id`, `--status`, `--limit`, `--handler`, `--yes`. |
| `stripe dispatches validate-fixtures` | None | None | `--path`. |
| `usage export-report` | Usage pane | None | TUI only reads existing artifacts; no report generation or options. |
| `usage sync-entitlements` | None | None | All flags: `--path`, `--plan`, `--prune-missing`, `--dry-run`, `--allow-disabled-artifact`. |
| `auth tokens issue-service-account` | None | None | All flags: `--account`, `--scopes`, `--tenant`, `--lifetime`, `--fingerprint`, `--force`, `--output`, `--base-url`. |
| `auth keys rotate` | None | None | `--kid`. |
| `auth jwks print` | None | None | (No args) |
| `config dump-schema` | None | None | `--format`. |
| `config write-inventory` | None | None | `--path`. |
| `api export-openapi` | None | None | `--output`, `--enable-billing`, `--enable-test-fixtures`, `--title`, `--version`. |
| `release db` | None | None | All flags: `--non-interactive`, `--skip-stripe`, `--skip-db-checks`, `--summary-path`, `--json`, `--plan`. |
| `start` | None | None | All flags: `target`, `--open-browser`, `--timeout`, `--skip-infra`, `--detached/--foreground`, `--force`, `--log-dir`, `--pidfile`. |
| `stop` | None | None | `--pidfile`. |
| `status subscriptions list` | None | None | `--limit`, `--cursor`, `--tenant`. |
| `status subscriptions revoke` | None | None | `subscription_id`. |
| `status incidents resend` | None | None | `incident_id`, `--severity`, `--tenant`. |
| `users ensure-dev` | None | None | All flags: `--email`, `--password`, `--tenant-slug`, `--tenant-name`, `--role`, `--display-name`, `--locked`, `--no-rotate-existing`. |
| `users seed` | None | None | All flags: `--email`, `--password`, `--tenant-slug`, `--tenant-name`, `--role`, `--display-name`, `--locked`, `--rotate-existing`, `--prompt-password`. |
| `util run-with-env` | None | None | All args: `env_files`, `exec_command`. |

## Notes / Design Considerations
- The Wizard pane already surfaces profile/preset/cloud/advanced, but not the headless CLI knobs (answers files, non-interactive mode, report-only, schema bypass, export paths, automation overrides).
- The Setup Hub pane uses the same detection logic as the CLI, but it does not execute command-based actions; it only navigates or prints the command string.
- Logs/Infra/Providers/Usage panes are snapshot/preview oriented; they do not expose the CLI’s export/scripting options.

